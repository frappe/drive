import os
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import shutil

import cv2
import frappe
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

        TEAMS = frappe.get_all("Drive Team", fields=["name", "s3_bucket"])
        self.bucket_map = {k["name"]: k["s3_bucket"] for k in TEAMS}

        if self.s3_enabled:
            import boto3
            from botocore.config import Config

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

    def resolve(self, path: str | Path) -> Path:
        """
        Return where `path` is on disk. Refuses anything outside the site's private files folder,
        such as paths with `..` or absolute paths.
        """
        root = self.site_folder.resolve()
        full_path = (root / path).resolve()
        if not full_path.is_relative_to(root):
            frappe.throw("This file is outside Drive's storage.", frappe.PermissionError)
        return full_path

    def get_bucket(self, team):
        return self.bucket_map.get(team) or self.bucket

    def can_create_thumbnail(self, file):
        # Don't create thumbnails for text files
        return (
            file.mime_type.startswith(("image", "video"))
            or file.mime_type == "application/pdf"
            or file.mime_type in FileManager.ACCEPTABLE_MIME_TYPES
        )

    def upload_file(self, current_path: Path, drive_file, create_thumbnail=True) -> None:
        """
        Moves the file from the current path to another path
        """
        # Never replace another file's bytes
        if self.exists(drive_file.team, drive_file.path):
            frappe.throw(f"Could not upload: '{drive_file.title}' already exists.", FileExistsError)
        if self.s3_enabled:
            self.conn.upload_file(current_path, self.get_bucket(drive_file.team), drive_file.path)
            if drive_file and create_thumbnail and self.can_create_thumbnail(drive_file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=drive_file,
                    file_path=str(current_path),
                )
            else:
                os.remove(current_path)
        else:
            # could break for folders?
            # Embeds go in the document's .embeds folder, which older documents may not have yet
            destination = self.resolve(drive_file.path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.rename(current_path, destination)
            if drive_file and create_thumbnail and self.can_create_thumbnail(drive_file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=drive_file,
                    file_path=str(destination),
                )

    def upload_thumbnail(self, file, file_path: str):
        """
        Creates a thumbnail for the file on disk and then uploads to the relevant team directory
        """
        save_path = self.get_thumbnail_path(file.team, file.name).with_suffix(".png")
        disk_path = str(self.resolve(save_path))

        try:
            with DistributedLock(file.path, exclusive=False):
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
            # broken: for docs, have to first create that folder
            parent = (
                Path(frappe.get_value("Drive File", entity.parent_entity, "path") or "")
                if not hasattr(entity, "parent_path")
                else Path(entity.parent_path)
            )
            if embed:
                return parent / ".embeds" / entity.title
            return parent / entity.title

    @__not_if_flat
    def create_folder(self, entity, root):
        """
        Function to create a folder in the S3 bucket or on disk.
        Only creates if flat structure is disabled.
        """
        path = self.get_disk_path(entity, root)
        if self.s3_enabled:
            self.conn.put_object(Bucket=self.get_bucket(entity.team), Key=str(path) + "/", Body="")
        else:
            self.resolve(path).mkdir(parents=True, exist_ok=True)
        return str(path) + "/"

    def get_file(self, entity, range_header=None):
        """
        Function to get a file, with an optional range header for S3 objects
        """
        try:
            if self.s3_enabled:
                if range_header:
                    buf = self.conn.get_object(
                        Bucket=self.get_bucket(entity.team), Key=entity.path, Range=range_header
                    )["Body"]
                else:
                    buf = self.conn.get_object(Bucket=self.get_bucket(entity.team), Key=entity.path)["Body"]
            else:
                with open(self.resolve(entity.path), "rb") as fh:
                    buf = BytesIO(fh.read())
        except frappe.PermissionError:
            raise
        except BaseException:
            frappe.throw("Could not find this file", frappe.NotFound)

        return buf

    def write_file(self, path: str | Path, content: str):
        if self.s3_enabled:
            pass
        else:
            with open(self.resolve(path), "w") as f:
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
            f = open(self.resolve(path), "rb")
            try:
                yield f
            finally:
                f.close()

    def get_thumbnail_path(self, team, name):
        return Path(get_home_folder(team)["path"]) / self.settings.thumbnail_prefix / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        return self.get_file(frappe._dict({"team": team, "path": str(self.get_thumbnail_path(team, name))}))

    def get_legacy_trash_path(self, entity: DriveFile):
        """Where items trashed before trash_path existed were put."""
        return Path(get_home_folder(entity.team)["path"]) / ".trash" / entity.title

    def exists(self, team, path: str | Path) -> bool:
        if self.s3_enabled:
            from botocore.exceptions import ClientError

            try:
                self.conn.head_object(Bucket=self.get_bucket(team), Key=str(path))
                return True
            except ClientError:
                return False
        return self.resolve(path).exists()

    def get_unused_path(self, team, path: Path) -> Path:
        """Return `path`, or `name (n).ext` next to it if something is already there."""
        candidate, n = path, 1
        while self.exists(team, candidate):
            candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
            n += 1
        return candidate

    @__not_if_flat
    def rename(self, entity):
        if not entity.path or entity.mime_type == "frappe/slides":
            return
        new_path = self.get_disk_path(entity)
        return self.move(entity, new_path)

    @__not_if_flat
    def move_to_trash(self, entity: DriveFile) -> str | None:
        """
        Move a file or folder into the team's .trash folder, under a name that is not taken.
        Returns where it was put, or None if there was nothing to move.
        """
        if not entity.path or entity.mime_type.startswith("frappe"):
            return None

        from botocore.exceptions import ClientError

        trash_path = self.get_unused_path(entity.team, self.get_legacy_trash_path(entity))
        try:
            self._move(entity.team, entity.path, trash_path)
        except (FileNotFoundError, ClientError):
            frappe.log_error(f"Moved {entity.name} to trash without it being on disk")
            return None
        return str(trash_path)

    @__not_if_flat
    def restore(self, entity: DriveFile, new_path: str | Path):
        """
        Move a file or folder from the trash to `new_path`.
        """
        trash_path = entity.trash_path
        if not trash_path:
            # Trashed before trash_path was stored
            trash_path = self.get_legacy_trash_path(entity)
            if entity.mime_type.startswith("frappe") or not self.exists(entity.team, trash_path):
                return
        self.move(frappe._dict(path=trash_path, team=entity.team), new_path)

    @__not_if_flat
    def move(self, entity, new_path: str | Path):
        """
        Move a file or folder. Never replaces anything at `new_path`.
        """
        from botocore.exceptions import ClientError

        try:
            self._move(entity.team, entity.path, new_path)
        except (FileNotFoundError, ClientError):
            frappe.throw("This file doesn't exist on disk.")
        return new_path

    def _move(self, team, path: str | Path, new_path: str | Path):
        """
        Move bytes without replacing anything, and move them back if the transaction is rolled back,
        so that disk and database stay in step.
        """
        if Path(path) == Path(new_path):
            return
        if self.exists(team, new_path):
            frappe.throw(f"Could not move: '{new_path}' already exists.", FileExistsError)
        self._move_object(team, path, new_path)

        def undo():
            try:
                self._move_object(team, new_path, path)
            except Exception:
                frappe.log_error(f"Could not move {new_path} back to {path} after a rollback")

        frappe.db.after_rollback.add(undo)

    def _move_object(self, team, path: str | Path, new_path: str | Path):
        if self.s3_enabled:
            bucket = self.get_bucket(team)
            self.conn.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": str(path)}, Key=str(new_path))
            self.conn.delete_object(Bucket=bucket, Key=str(path))
        else:
            source = self.resolve(path)
            if not source.exists():
                raise FileNotFoundError(source)
            destination = self.resolve(new_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source, destination)

    def delete_file(self, entity):
        thumbnail_path = self.get_thumbnail_path(entity.team, entity.name)

        if self.s3_enabled:
            bucket = self.get_bucket(entity.team)
            try:
                self.conn.delete_object(Bucket=bucket, Key=entity.path)
                if thumbnail_path:
                    self.conn.delete_object(Bucket=bucket, Key=str(thumbnail_path))
            except:
                pass
        else:
            try:
                self.resolve(entity.path).unlink()
                if thumbnail_path:
                    self.resolve(thumbnail_path).unlink()
            except FileNotFoundError:
                pass
