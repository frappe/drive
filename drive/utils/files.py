import os
from io import BytesIO
from pathlib import Path

import boto3
import cv2
import frappe
import magic
import mimemapper
from botocore.config import Config
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
        self.team_prefix = settings.team_prefix
        self.personal_prefix = settings.personal_prefix
        self.site_folder = Path(frappe.get_site_path("private/files"))
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
            self.conn.upload_file(current_path, self.bucket, drive_file.path)
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
                final_path = disk_path.with_suffix(".thumbnail")
                if self.s3_enabled:
                    # Removes original file
                    os.remove(file_path)
                    self.conn.upload_file(final_path, self.bucket, final_path)
                    disk_path.unlink()
                else:
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
                Path(frappe.get_value("Drive File", entity.parent_entity, "path"))
                if not hasattr(entity, "parent_path")
                else Path(entity.parent_path)
            )
            if root["name"] == entity.parent_entity:
                # Root files are placed in either team or personal folders
                if entity.is_private:
                    user_folder = parent / self.personal_prefix / frappe.session.user
                    if not self.s3_enabled and not (self.site_folder / user_folder).exists():
                        (self.site_folder / user_folder).mkdir()
                        (self.site_folder / user_folder / ".thumbnails").mkdir()
                    path = user_folder / entity.title
                else:
                    path = parent / self.team_prefix / entity.title
            else:
                # Otherwise, rely on the parent already having a perms-adjusted path
                path = parent / entity.title
            return path

    @__not_if_flat
    def create_folder(self, drive_entity, root):
        """
        Function to create a folder in the S3 bucket or on disk.
        Only creates if flat structure is disabled.
        """
        path = self.get_disk_path(drive_entity, root)
        if self.s3_enabled:
            self.conn.put_object(Bucket=self.bucket, Key=str(path) + "/", Body="")
        else:
            (self.site_folder / path).mkdir()

        return path

    def get_file(self, path):
        """
        Function to read file from a s3 file.

        Temporary: if not found in S3, look at disk.
        """
        if self.s3_enabled:
            try:
                buf = self.conn.get_object(Bucket=self.bucket, Key=path)["Body"]
            except:
                raise FileNotFoundError("Cannot find this file in the S3 bucket.")
        else:
            with open(self.site_folder / path, "rb") as fh:
                buf = BytesIO(fh.read())

        return buf

    def fetch_new_files(self, team: str) -> dict[Path, tuple[str]]:
        """
        Traverse the site folder and return a list of all yet-uncreated files with information
        Returns path, location (team or personal), file size, and modified
        Ignores hidden files
        """
        root_folder = Path(get_home_folder(team)["path"])
        if self.s3_enabled:
            objects = self.conn.list_objects_v2(Bucket=self.bucket).get("Contents", [])
            basic_files = {}

            # Get files...
            for obj in objects:
                obj_path = Path(obj["Key"])
                personal = False
                if obj_path.is_relative_to(root_folder / self.team_prefix):
                    basic_files[obj["Key"]] = (obj, "team")
                elif obj_path.is_relative_to(root_folder / self.personal_prefix):
                    # TBD
                    basic_files[obj["Key"]] = (obj, "personal")
                    personal = "personal"

                # Used to "calculate" natural folders, folders created by Drive are already counted
                # Don't count root folder
                parent_path = obj_path.parent
                if parent_path not in basic_files and parent_path != Path("."):
                    parent_obj = {
                        "Key": str(parent_path),
                        "Size": 0,
                        "LastModified": obj["LastModified"],
                        "Folder": True,
                    }
                    basic_files[parent_obj["Key"]] = (
                        parent_obj,
                        personal if personal else "team",
                    )

            files = {}
            for f_path, (f, loc) in basic_files.items():
                # Drive-created folders - registered S3 objects - have trailing slashes.
                is_group = f.get("Folder") or f_path.endswith("/")
                exists = frappe.get_value(
                    "Drive File",
                    {
                        "path": f_path.rstrip("/"),
                        "team": team,
                        "is_active": 1,
                        "is_group": int(is_group),
                    },
                    "name",
                )
                if exists:
                    continue

                mime_type = (
                    "folder"
                    if is_group
                    else mimemapper.get_mime_type(str(f_path), native_first=False)
                )
                files[Path(f_path)] = (loc, f["Size"], f["LastModified"].timestamp(), mime_type)
        else:
            root_folder = self.site_folder / root_folder
            # Get files...
            team_files = {f: "team" for f in (root_folder / self.team_prefix).glob("**/*")}

            personal_files = {}
            if self.personal_prefix:
                personal_users = [
                    f.name for f in (root_folder / self.personal_prefix).iterdir() if f.is_dir()
                ]
                for user in personal_users:
                    user_folder = root_folder / self.personal_prefix / user
                    for f in user_folder.glob("**/*"):
                        personal_files[f] = user

            # ... and stitch them together with information
            files = {}
            for f, loc in (team_files | personal_files).items():
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

                files[path] = (loc, f.stat().st_size, f.stat().st_mtime, mime_type)
        return files

    def get_thumbnail_path(self, team, name):
        return (
            self.get_disk_path(
                frappe.get_cached_doc("Drive File", {"name": name, "team": team})
            ).parent
            / self.settings.thumbnail_prefix
            / (name + ".thumbnail")
        )

    def get_old_thumbnail_path(self, team, name):
        return Path(get_home_folder(team)["path"]) / "thumbnails" / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        # Used for pre v-0.3 compatibility
        try:
            return self.get_file(str(self.get_thumbnail_path(team, name)))
        except:
            return self.get_file(str(self.get_old_thumbnail_path(team, name)))

    def __get_trash_path(self, entity: DriveFile):
        root = get_home_folder(entity.team)
        if entity.is_private:
            trash_path = (
                Path(root["path"])
                / self.personal_prefix
                / frappe.session.user
                / ".trash"
                / entity.title
            )
        else:
            trash_path = Path(root["path"]) / self.team_prefix / ".trash" / entity.title
        return trash_path

    def get_parent_path(self, path: Path, team, is_private: bool) -> Path:
        """
        Function to get the DB parent path for a given file or folder
        Used because root files are placed in either team or personal folders, but DB path is shared.
        """
        disk_parent = path.parent
        root = Path(get_home_folder(team)["path"])
        if not is_private and root / self.team_prefix == disk_parent:
            disk_parent = root
        elif is_private and root / self.personal_prefix == disk_parent.parent:
            disk_parent = root
        return disk_parent if disk_parent != Path(".") else ""

    @__not_if_flat
    def rename(self, entity):
        new_path = self.get_disk_path(entity)
        return self.move(entity.path, new_path)

    @__not_if_flat
    def move_to_trash(self, entity: DriveFile):
        trash_path = self.__get_trash_path(entity)
        try:
            if self.s3_enabled:
                self.conn.copy_object(
                    Bucket=self.bucket,
                    CopySource={"Bucket": self.bucket, "Key": entity.path},
                    Key=str(trash_path),
                )
                self.conn.delete_object(Bucket=self.bucket, Key=entity.path)
            else:
                full_trash_path = self.site_folder / trash_path
                full_trash_path.parent.mkdir(exist_ok=True)
                (self.site_folder / entity.path).rename(full_trash_path)
        except FileNotFoundError:
            pass

    @__not_if_flat
    def restore(self, entity: DriveFile):
        """
        Restore a file from the trash.
        """
        current_path = self.__get_trash_path(entity)
        self.move(str(current_path), entity.path)

    @__not_if_flat
    def move(self, old_path: str, new_path: str):
        """
        Move a file on disk
        """
        try:
            if self.s3_enabled:
                self.conn.copy_object(
                    Bucket=self.bucket,
                    CopySource={"Bucket": self.bucket, "Key": old_path},
                    Key=new_path,
                )
                self.conn.delete_object(Bucket=self.bucket, Key=old_path)
            else:
                (self.site_folder / old_path).rename(self.site_folder / new_path)
        except:
            frappe.throw("This file doesn't exist on disk.")
        return new_path

    def delete_file(self, team, name, path):
        if self.s3_enabled:
            self.conn.delete_object(Bucket=self.bucket, Key=path)
        else:
            try:
                (self.site_folder / path).unlink()
                self.get_thumbnail_path(team, name).unlink()
            except FileNotFoundError:
                pass
