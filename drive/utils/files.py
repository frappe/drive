import os
from io import BytesIO
from pathlib import Path

import boto3
import cv2
import frappe
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
        self.s3_enabled = settings.enabled
        self.flat = settings.flat
        self.bucket = settings.bucket
        self.site_folder = Path(frappe.get_site_path("private/files"))
        if self.s3_enabled:
            self.conn = boto3.client(
                "s3",
                aws_access_key_id=settings.aws_key,
                aws_secret_access_key=settings.get_password("aws_secret"),
                endpoint_url=(settings.endpoint_url or None),
                config=Config(signature_version=settings.signature_version),
            )

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
        team_directory = get_home_folder(file.team)["name"]
        save_path = Path(team_directory) / "thumbnails" / (file.name + ".png")
        disk_path = str((self.site_folder / save_path).resolve())

        with DistributedLock(file.path, exclusive=False):
            try:
                # Keep image/video thumbnail as `thumbnail` results in very dark thumbnails (albeit better)
                if file.mime_type.startswith("image"):
                    with Image.open(file_path).convert("RGB") as image:
                        image = ImageOps.exif_transpose(image)
                        image.thumbnail((512, 512))
                        image.save(str(disk_path), format="webp")
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
                final_path = Path(disk_path)
                if self.s3_enabled:
                    os.remove(file_path)
                    self.conn.upload_file(
                        final_path, self.bucket, str(save_path.with_suffix(".thumbnail"))
                    )
                    final_path.unlink()
                else:
                    final_path.rename(final_path.with_suffix(".thumbnail"))

            except Exception:
                if self.s3_enabled:
                    try:
                        os.remove(file_path)
                    except FileNotFoundError:
                        pass

    def get_disk_path(self, entity, root):
        """
        Helper function to get path of a file
        """
        if self.flat:
            return self.site_folder / entity.parent_path / entity.name
        else:
            parent = (
                Path(frappe.get_value("Drive File", entity.parent_entity, "path"))
                if not hasattr(entity, "parent_path")
                else Path(entity.parent_path)
            )
            if root:
                # Root files are placed in either team or personal folders
                if entity.is_private:
                    path = parent / "personal" / frappe.session.user / entity.title
                else:
                    path = parent / "team" / entity.title
            else:
                # Otherwise, rely on the parent already having a perms-adjusted path
                path = parent / entity.title
            return str(path) + "/"

    def create_folder(self, drive_entity, root):
        """
        Function to create a folder in the S3 bucket or on disk.
        Only creates if flat structure is disabled.
        """
        if self.flat:
            return
        else:
            path = self.get_disk_path(drive_entity, root)
            if self.s3_enabled:
                self.conn.put_object(Bucket=self.bucket, Key=path, Body="")
            else:
                (self.site_folder / path).mkdir(parents=True, exist_ok=True)

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
                return ""
        else:
            with DistributedLock(path, exclusive=False):
                with open(self.site_folder / path, "rb") as fh:
                    buf = BytesIO(fh.read())

        return buf

    def get_thumbnail_path(self, team, name):
        return Path(get_home_folder(team)["name"]) / "thumbnails" / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        return self.get_file(str(self.get_thumbnail_path(team, name)))

    def delete_file(self, team, name, path):
        if self.s3_enabled:
            self.conn.delete_object(Bucket=self.bucket, Key=path)
        else:
            try:
                (self.site_folder / path).unlink()
                self.get_thumbnail_path(team, name).unlink()
            except FileNotFoundError:
                pass
