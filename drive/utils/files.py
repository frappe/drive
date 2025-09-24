import os
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import boto3
import cv2
import frappe
import magic
import mimemapper
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image, ImageOps

from drive.locks.distributed_lock import DistributedLock

from . import get_home_folder

DriveFile = frappe.qb.DocType("Drive File")


class FileManager:
    ACCEPTABLE_MIME_TYPES = [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
    ]

    def __init__(self):
        settings = frappe.get_single("Drive Disk Settings")
        self.settings = settings
        self.s3_enabled = settings.enabled
        self.flat = settings.flat
        self.bucket = settings.bucket
        self.site_folder = Path(frappe.get_site_path("private/files"))

        TEAMS = frappe.get_all("Drive Team", fields=["name", "s3_bucket", "prefix"])
        self.bucket_map = {k["name"]: k["s3_bucket"] for k in TEAMS}
        self.prefix_map = {k["name"]: k["prefix"] for k in TEAMS}

        if self.s3_enabled:
            self.conn = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_key,
                aws_secret_access_key=settings.get_password("aws_secret"),
                endpoint_url=(settings.endpoint_url or None),
                config=Config(signature_version=settings.signature_version),
            )

    def __not_if_flat(func):
        """
        Decorator to skip the function if flat structure is enabled.
        """

        def wrapper(self, *args, **kwargs):
            if self.flat:
                return
            return func(self, *args, **kwargs)

        return wrapper

    def get_bucket(self, team):
        return self.bucket_map.get(team) or self.bucket

    def get_prefix(self, team):
        prefix = self.prefix_map.get(team)
        if prefix is None:
            return self.settings.root_folder
        return prefix

    def can_create_thumbnail(self, file):
        # Don't create thumbnails for text files
        return (
            file.mime_type.startswith(("image", "video"))
            or file.mime_type == "application/pdf"
            or file.mime_type in FileManager.ACCEPTABLE_MIME_TYPES
        )

    def upload_file(self, current_path: Path, drive_file) -> None:
        """
        Moves the file from the current path to another path
        """
        if self.s3_enabled:
            self.conn.upload_file(current_path, self.get_bucket(drive_file.team), drive_file.path)
            if drive_file and self.can_create_thumbnail(drive_file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=drive_file,
                    file_path=current_path,
                )
            else:
                os.remove(current_path)
        else:
            os.rename(current_path, self.site_folder / drive_file.path)
            if drive_file and self.can_create_thumbnail(drive_file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=drive_file,
                    file_path=str(self.site_folder / drive_file.path),
                )

    def upload_thumbnail(self, file, file_path: str):
        """
        Creates a thumbnail for the file on disk and then uploads to the relevant team directory
        """
        save_path = self.get_thumbnail_path(file.team, file.name).with_suffix(".png")
        disk_path = str(self.site_folder / save_path)

        with DistributedLock(file.path, exclusive=False):
            try:
                # Keep image/video thumbnail as `thumbnail` results in very dark thumbnails (albeit better)
                if file.mime_type.startswith("image"):
                    with Image.open(file_path).convert("RGB") as image:
                        image = ImageOps.exif_transpose(image)
                        image.thumbnail((512, 512))
                        image.save(disk_path, format="webp")
                elif file.mime_type.startswith("video"):
                    cap = cv2.VideoCapture(file_path)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    target_frame = int(frame_count / 2)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    _, frame = cap.read()
                    cap.release()
                    _, thumbnail_encoded = cv2.imencode(
                        ".webp",
                        frame,
                        [int(cv2.IMWRITE_WEBP_QUALITY), 50],
                    )
                    with open(disk_path, "wb") as f:
                        f.write(thumbnail_encoded)
                else:
                    from thumbnail import generate_thumbnail

                    # Word document thumbnail
                    generate_thumbnail(
                        file_path,
                        disk_path,
                        {
                            "trim": False,
                            "height": 512,
                            "width": 512,
                            "quality": 100,
                            "type": "thumbnail",
                        },
                    )

                disk_path = Path(disk_path)
                if self.s3_enabled:
                    # Removes original file
                    os.remove(file_path)
                    self.conn.upload_file(
                        disk_path, self.get_bucket(file.team), str(save_path.with_suffix(".thumbnail"))
                    )
                    disk_path.unlink()
                else:
                    final_path = disk_path.with_suffix(".thumbnail")
                    disk_path.rename(final_path)

            except BaseException as e:
                frappe.log_error("Thumbnail failed", e)
                if self.s3_enabled:
                    try:
                        os.remove(file_path)
                    except FileNotFoundError:
                        pass

    def get_disk_path(self, entity: DriveFile, root: dict = None, embed=False):
        """
        Helper function to get path of a file
        """
        if not root:
            root = get_home_folder(entity.team)

        if self.flat:
            return Path(root["path"]) / (Path("embeds") / entity.name if embed else entity.name)
        else:
            # perf: stupidly complicated because we use this both with a real entity and a dict
            parent = (
                Path(frappe.get_value("Drive File", entity.parent_entity, "path") or "")
                if not hasattr(entity, "parent_path")
                else Path(entity.parent_path)
            )
            return parent / entity.title

    @__not_if_flat
    def create_folder(self, entity, root):
        """
        Function to create a folder in the S3 bucket or on disk.
        Only creates if flat structure is disabled.
        """
        path = self.get_disk_path(entity, root)
        print(self.conn.list_objects_v2(Bucket=self.get_bucket(entity.team)))
        if self.s3_enabled:
            self.conn.put_object(Bucket=self.get_bucket(entity.team), Key=str(path) + "/", Body="")
        else:
            (self.site_folder / path).mkdir()
        return str(path) + ("/" if entity.is_group else "")

    def get_file(self, entity):
        """
        Function to read file from a s3 file.

        Temporary: if not found in S3, look at disk.
        """
        if self.s3_enabled:
            try:
                print(self.get_bucket(entity.team), entity.path)
                buf = self.conn.get_object(Bucket=self.get_bucket(entity.team), Key=entity.path)["Body"]
            except:
                raise FileNotFoundError("Cannot find this file in the S3 bucket.")
        else:
            with open(self.site_folder / entity.path, "rb") as fh:
                buf = BytesIO(fh.read())

        return buf

    def write_file(self, path: str | Path, content: str):
        if self.s3_enabled:
            pass
        else:
            with open(self.site_folder / path, "w") as f:
                f.write(content)

    @contextmanager
    def open_file(self, path):
        """
        Context manager that yields a file-like object.
        - On disk: opens in binary mode, closes automatically.
        - On S3: yields the botocore StreamingBody, closes automatically.
        """
        if self.s3_enabled:
            obj = self.conn.get_object(Bucket=self.bucket, Key=path)
            body = obj["Body"]
            try:
                yield body  # StreamingBody is already a file-like object
            finally:
                body.close()
        else:
            f = open(self.site_folder / path, "rb")
            try:
                yield f
            finally:
                f.close()

    def fetch_new_files(self, team) -> dict[Path, tuple[str]]:
        """
        Traverse the site folder and return a list of all yet-uncreated files with information
        Returns path, location (team or personal), file size, and modified
        Ignores hidden files
        """
        root_folder = self.get_prefix(team)
        if self.s3_enabled:
            objects = self.conn.list_objects_v2(Bucket=self.get_bucket(team)).get("Contents", [])
            basic_files = {}

            # Get files...
            for obj in objects:
                obj_path = Path(obj["Key"])

                if not obj_path.is_relative_to(root_folder) or any(str(p).startswith(".") for p in obj_path.parts):
                    continue
                basic_files[obj_path] = obj

                # Used to "calculate" natural folders, folders created by Drive are already counted
                # Don't count root folder
                parent_path = obj_path.parent
                if obj_path not in basic_files and parent_path != Path("."):
                    basic_files[parent_path] = {
                        "Key": str(parent_path),
                        "Size": 0,
                        "LastModified": obj["LastModified"],
                        "Folder": True,
                    }

            files = {}

            for f in basic_files.values():
                # Drive-created folders - registered S3 objects - have trailing slashes.
                is_group = f.get("Folder") or f["Key"].endswith("/")
                exists = frappe.get_value(
                    "Drive File",
                    {
                        "path": f["Key"].rstrip("/") + ("/" if is_group else ""),
                        "is_active": 1,
                        "team": team,
                        "is_group": int(is_group),
                    },
                    "name",
                )
                if exists:
                    continue

                mime_type = "folder" if is_group else mimemapper.get_mime_type(str(f["Key"]), native_first=False)
                files[Path(f["Key"])] = (f["Size"], f["LastModified"].timestamp(), mime_type)
        else:
            root_folder = self.site_folder / self.get_prefix(team)

            # ... and stitch them together with information
            files = {}
            for f in root_folder.glob("**/*"):
                path = f.relative_to(self.site_folder)
                exists = frappe.get_value(
                    "Drive File",
                    {"path": str(path), "team": team, "is_active": 1},
                    "name",
                )
                if exists or any(p for p in f.parts if p.startswith(".")):
                    continue

                if f.is_dir():
                    mime_type = "folder"
                else:
                    mime_type = mimemapper.get_mime_type(str(f), native_first=False)
                if mime_type is None:
                    mime_type = magic.from_buffer(open(f, "rb").read(2048), mime=True)

                files[path] = (f.stat().st_size, f.stat().st_mtime, mime_type)
        return files

    def get_thumbnail_path(self, team, name):
        return Path(get_home_folder(team)["path"]) / self.settings.thumbnail_prefix / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        return self.get_file(frappe._dict({"team": team, "path": str(self.get_thumbnail_path(team, name))}))

    def __get_trash_path(self, entity: DriveFile):
        root = get_home_folder(entity.team)
        return Path(root["path"]) / ".trash" / entity.title

    @__not_if_flat
    def rename(self, entity):
        if not entity.path or entity.mime_type.startswith("frappe"):
            return
        new_path = self.get_disk_path(entity)
        return self.move(entity.path, new_path)

    @__not_if_flat
    def move_to_trash(self, entity: DriveFile):
        if not entity.path or entity.mime_type.startswith("frappe"):
            return

        trash_path = self.__get_trash_path(entity)
        try:
            if self.s3_enabled:
                bucket = self.get_bucket(entity.team)
                self.conn.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": entity.path},
                    Key=str(trash_path),
                )
                self.conn.delete_object(Bucket=bucket, Key=entity.path)
            else:
                full_trash_path = self.site_folder / trash_path
                full_trash_path.parent.mkdir(exist_ok=True)
                (self.site_folder / entity.path).rename(full_trash_path)
        except (FileNotFoundError, ClientError):
            frappe.log_error(f"Moved {entity.name} to trash without it being on disk")
            pass

    @__not_if_flat
    def restore(self, entity: DriveFile):
        """
        Restore a file from the trash.
        """
        current_path = self.__get_trash_path(entity)
        self.move(str(current_path), entity.path)

    @__not_if_flat
    def move(self, old_path: str | Path, new_path: str):
        """
        Move a file on disk
        """
        try:
            if self.s3_enabled:
                bucket = self.get_bucket(entity.team)
                self.conn.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": old_path},
                    Key=new_path,
                )
                self.conn.delete_object(Bucket=bucket, Key=old_path)
            else:
                (self.site_folder / old_path).rename(self.site_folder / new_path)
        except BaseException as e:
            frappe.throw("This file doesn't exist on disk.")
        return new_path

    def delete_file(self, entity):
        thumbnail_path = self.get_thumbnail_path(entity.team, entity.name)
        if self.s3_enabled:
            bucket = self.get_bucket(entity.team)
            self.conn.delete_object(Bucket=bucket, Key=entity.path)
            self.conn.delete_object(Bucket=bucket, Key=str(thumbnail_path))
        else:
            try:
                (self.site_folder / entity.path).unlink()
                thumbnail_path.unlink()
            except FileNotFoundError:
                pass
