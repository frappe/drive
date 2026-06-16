import os
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import shutil
from urllib.parse import unquote

import boto3
import frappe
import mimemapper
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image, ImageOps

from drive.locks.distributed_lock import DistributedLock

from . import get_home_folder, STATUS_ACTIVE

S3_URL_PREFIX = "/api/method/drive.api.s3.fetch?path="


class FileManager:
    def __init__(self):
        settings = frappe.get_single("Drive Disk Settings")
        self.settings = settings
        self.s3_enabled = settings.enabled
        self.flat = settings.flat
        self.bucket = settings.bucket
        self.site_folder = Path(frappe.get_site_path())

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

    def _not_if_flat(func):
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
        # Only images, videos and PDFs get thumbnails.
        if not hasattr(file, "mime_type"):
            return False
        return file.mime_type.startswith(("image", "video")) or file.mime_type == "application/pdf"

    def upload_file(self, current_path: Path, file, create_thumbnail=True) -> None:
        """
        Moves the file from the current path to another path
        """
        if self.s3_enabled:
            self.conn.upload_file(current_path, self.get_bucket(file.team), get_s3_key(file.file_url))
            if create_thumbnail and self.can_create_thumbnail(file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=file,
                    file_path=str(current_path),
                )
            else:
                os.remove(current_path)
        else:
            os.rename(current_path, self.site_folder / storage_key(file.file_url))
            if file and create_thumbnail and self.can_create_thumbnail(file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=file,
                    file_path=str(self.site_folder / storage_key(file.file_url)),
                )

    def upload_thumbnail(self, file, file_path: str):
        """
        Creates a thumbnail for the file on disk and then uploads to the relevant team directory
        """
        save_path = self.get_thumbnail_path(file.team, file.name).with_suffix(".png")
        disk_path = str(self.site_folder / save_path)

        try:
            with DistributedLock(file_path, exclusive=False):
                if file.mime_type.startswith("image"):
                    with Image.open(file_path).convert("RGB") as image:
                        image = ImageOps.exif_transpose(image)
                        image.thumbnail((512, 512))
                        image.save(disk_path, format="webp")
                elif file.mime_type.startswith("video"):
                    import av

                    with av.open(file_path) as container:
                        stream = container.streams.video[0]
                        if stream.duration:
                            container.seek(stream.duration // 2, stream=stream)
                        image = next(container.decode(stream)).to_image()
                        image.thumbnail((512, 512))
                        image.save(disk_path, format="webp")
                else:
                    import pymupdf

                    with pymupdf.open(file_path) as pdf:
                        page = pdf.load_page(0)
                        zoom = 512 / max(page.rect.width, page.rect.height)
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
                        Image.frombytes("RGB", (pix.width, pix.height), pix.samples).save(
                            disk_path, format="webp"
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

    def get_disk_path(self, entity, root: dict = None, embed=False):
        """
        Helper function to get path of a file
        """
        if self.flat:
            if not root:
                root = get_home_folder(entity.team)
            return Path(storage_key(root["file_url"])) / (Path("embeds") / entity.name if embed else entity.name)
        else:
            # perf: stupidly complicated because we use this both with a real entity and a dict
            parent = (
                Path(storage_key(frappe.get_value("File", entity.folder, "file_url") or ""))
                if not hasattr(entity, "parent_path")
                else Path(entity.parent_path)
            )
            if embed:
                return parent / ".embeds" / entity.file_name
            return parent / entity.file_name

    @_not_if_flat
    def create_folder(self, entity, root):
        """
        Function to create a folder in the S3 bucket or on disk.
        Only creates if flat structure is disabled.
        """
        path = self.get_disk_path(entity, root)
        if self.s3_enabled:
            self.conn.put_object(Bucket=self.get_bucket(entity.team), Key=str(path) + "/", Body="")
        else:
            (self.site_folder / path).mkdir()
        return str(path) + "/"

    def get_file(self, entity, range_header=None, log=True):
        """
        Function to get a file, with an optional range header for S3 objects
        """
        file_url = storage_key(entity.file_url)
        try:
            if self.s3_enabled:
                if range_header:
                    buf = self.conn.get_object(Bucket=self.get_bucket(entity.team), Key=file_url, Range=range_header)[
                        "Body"
                    ]
                else:
                    buf = self.conn.get_object(Bucket=self.get_bucket(entity.team), Key=file_url)["Body"]
            else:
                with open(self.site_folder / file_url, "rb") as fh:
                    buf = BytesIO(fh.read())
        except (ClientError, FileNotFoundError, OSError) as e:
            if log:
                frappe.log_error("Drive: could not read file", e)
            frappe.throw("Could not find this file.", frappe.DoesNotExistError)

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
        if self.s3_enabled:
            root_folder = Path(self.get_prefix(team))
            objects = self.conn.list_objects_v2(Bucket=self.get_bucket(team)).get("Contents", [])
            basic_files = {}

            # Get files...
            for obj in objects:
                obj_path = Path(obj["Key"])

                if (
                    not obj_path.is_relative_to(root_folder)
                    or obj_path == root_folder
                    or any(str(p).startswith(".") for p in obj_path.parts)
                ):
                    continue
                obj_path = obj_path.relative_to(root_folder)
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

            for path, f in basic_files.items():
                # Drive-created folders - registered S3 objects - have trailing slashes.
                is_folder = f.get("Folder") or f["Key"].endswith("/")
                exists = frappe.get_value(
                    "File",
                    {
                        "file_url": f["Key"].rstrip("/") + ("/" if is_folder else ""),
                        "status": STATUS_ACTIVE,
                        "team": team,
                        "is_folder": int(is_folder),
                    },
                    "name",
                )
                if exists:
                    continue

                mime_type = "folder" if is_folder else mimemapper.get_mime_type(f["Key"], native_first=False)
                # Team path is key, DB path is f["Key"]
                files[path] = (f["Size"], f["LastModified"].timestamp(), mime_type, f["Key"])
        else:
            root_folder = self.site_folder / self.get_prefix(team)

            # ... and stitch them together with information
            files = {}
            for f in root_folder.glob("**/*"):
                path = f.relative_to(self.site_folder)
                exists = frappe.get_value(
                    "File",
                    {"file_url": str(path), "team": team, "status": STATUS_ACTIVE},
                    "name",
                )
                if exists or any(p for p in f.parts if p.startswith(".")):
                    continue

                if f.is_dir():
                    mime_type = "folder"
                else:
                    mime_type = mimemapper.get_mime_type(str(f), native_first=False)

                # Twice `path` for compatability with S3 format
                files[path] = (f.stat().st_size, f.stat().st_mtime, mime_type, str(path))

        return files

    def get_thumbnail_path(self, team, name):
        return Path(storage_key(get_home_folder(team)["file_url"])) / self.settings.thumbnail_prefix / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        return self.get_file(
            frappe._dict({"team": team, "file_url": str(self.get_thumbnail_path(team, name))}), log=False
        )

    def __get_trash_path(self, entity):
        root = get_home_folder(entity.team)
        return Path(storage_key(root["file_url"])) / ".trash" / entity.file_name

    @_not_if_flat
    def rename(self, entity):
        if not entity.file_url or entity.mime_type == "frappe/slides":
            return
        new_path = self.get_disk_path(entity)
        return self.move(entity, new_path)

    @_not_if_flat
    def move_to_trash(self, entity):
        if not entity.file_url or entity.mime_type in ["frappe/slides", "link"]:
            return

        trash_path = self.__get_trash_path(entity)
        try:
            if self.s3_enabled:
                bucket = self.get_bucket(entity.team)
                self.conn.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": storage_key(entity.file_url)},
                    Key=str(trash_path),
                )
                self.conn.delete_object(Bucket=bucket, Key=storage_key(entity.file_url))
            else:
                full_trash_path = self.site_folder / trash_path
                if full_trash_path.exists() and full_trash_path.is_dir():
                    shutil.rmtree(full_trash_path)

                full_trash_path.parent.mkdir(exist_ok=True)
                cur_path = self.site_folder / storage_key(entity.file_url)
                if cur_path.is_dir():
                    shutil.move(cur_path, full_trash_path)
                else:
                    cur_path.rename(full_trash_path)
        except (FileNotFoundError, ClientError):
            frappe.log_error(f"Moved {entity.name} to trash without it being on disk")
            pass

    @_not_if_flat
    def restore(self, entity):
        """
        Restore a file from the trash.
        """
        self.move(frappe._dict(file_url=self.__get_trash_path(entity), team=entity.team), entity.file_url)

    @_not_if_flat
    def move(self, entity, new_path: str | Path):
        """
        Move a file on disk
        """
        # Callers pass new_path as either a bare key or a stored file_url;
        # normalize both ends to the actual backend key.
        src_key = storage_key(entity.file_url)
        dest_key = storage_key(new_path)
        try:
            if self.s3_enabled:
                bucket = self.get_bucket(entity.team)
                self.conn.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": src_key},
                    Key=dest_key,
                )
                self.conn.delete_object(Bucket=bucket, Key=src_key)
            else:
                cur_path = self.site_folder / src_key
                dest_path = self.site_folder / dest_key
                if cur_path.is_dir():
                    shutil.move(cur_path, dest_path)
                else:
                    cur_path.rename(dest_path)
        except BaseException as e:
            frappe.throw("This file doesn't exist on disk.")
        return new_path

    def delete_file(self, entity):
        thumbnail_path = self.get_thumbnail_path(entity.team, entity.name)

        if self.s3_enabled:
            bucket = self.get_bucket(entity.team)
            try:
                self.conn.delete_object(Bucket=bucket, Key=storage_key(entity.file_url))
                if thumbnail_path:
                    self.conn.delete_object(Bucket=bucket, Key=str(thumbnail_path))
            except:
                pass
        else:
            try:
                (self.site_folder / storage_key(entity.file_url)).unlink()
                if thumbnail_path:
                    (self.site_folder / thumbnail_path).unlink()
            except FileNotFoundError:
                pass


# Utils
def storage_key(file_url):
    # file_url -> backend storage key, always relative so `base / key` can't
    # reset to an absolute path (Path("a") / "/b" == Path("/b")).
    file_url = str(file_url)
    if file_url.startswith(S3_URL_PREFIX):
        return unquote(file_url[len(S3_URL_PREFIX) :])
    return file_url.lstrip("/")


def get_s3_key(file_url):
    prefixes = ["/private/files/", "/files/"]
    for prefix in prefixes:
        if file_url.startswith(prefix):
            return file_url[len(prefix) :]
    return file_url


def get_s3_url(path):
    from urllib.parse import quote

    return S3_URL_PREFIX + quote(path)
