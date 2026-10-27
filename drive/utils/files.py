import os
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import shutil
from urllib.parse import unquote

import frappe
from PIL import Image, ImageOps

from drive.locks.distributed_lock import DistributedLock

from . import get_home_folder

S3_URL_PREFIX = "/api/method/drive.api.s3.fetch?path="


def _get_s3_client(settings):
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_key,
        aws_secret_access_key=settings.get_password("aws_secret"),
        endpoint_url=(settings.endpoint_url or None),
        config=Config(signature_version=settings.signature_version),
    )


def _get_s3_client_errors():
    try:
        from botocore.exceptions import ClientError
    except ImportError:
        return ()

    return (ClientError,)


class FileManager:
    def __init__(self):
        settings = frappe.get_single("Drive Disk Settings")
        self.settings = settings
        self.s3_enabled = settings.enabled
        self.flat = settings.flat
        self.bucket = settings.bucket
        self.site_folder = Path(frappe.get_site_path())
        self.s3_errors = ()

        TEAMS = frappe.get_all("Drive Team", fields=["name", "s3_bucket"])
        self.bucket_map = {k["name"]: k["s3_bucket"] for k in TEAMS}

        if self.s3_enabled:
            self.s3_errors = _get_s3_client_errors()
            self.conn = _get_s3_client(settings)

    def _not_if_flat(func):
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
        Return where a storage key is on disk. Refuses anything outside the site's private files folder,
        such as keys with `..`, or links that lead elsewhere.
        """
        root = (self.site_folder / "private" / "files").resolve()
        full_path = (self.site_folder.resolve() / storage_key(path)).resolve()
        if not full_path.is_relative_to(root):
            frappe.throw("This file is outside Drive's storage.", frappe.PermissionError)
        return full_path

    def get_bucket(self, team):
        return self.bucket_map.get(team) or self.bucket

    def can_create_thumbnail(self, file):
        # Only images, videos and PDFs get thumbnails.
        if not hasattr(file, "mime_type"):
            return False
        return file.mime_type.startswith(("image", "video")) or file.mime_type == "application/pdf"

    def upload_file(self, current_path: Path, file, create_thumbnail=True) -> None:
        """
        Moves the file from the current path to another path
        """
        # Never replace another file's bytes
        stored_path = get_s3_url(get_s3_key(file.file_url)) if self.s3_enabled else file.file_url
        if self.exists(file.team, stored_path):
            frappe.throw(f"Could not upload: '{file.file_name}' already exists.", FileExistsError)
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
            # Embeds go in a .embeds folder, which may not exist yet
            destination = self.resolve(file.file_url)
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Link, then remove the temporary name. Unlike a rename, linking fails if another upload got there first.
            try:
                os.link(current_path, destination)
            except FileExistsError:
                os.remove(current_path)
                frappe.throw(f"Could not upload: '{file.file_name}' already exists.", FileExistsError)
            os.remove(current_path)
            if file and create_thumbnail and self.can_create_thumbnail(file):
                frappe.enqueue(
                    self.upload_thumbnail,
                    now=True,
                    at_front=True,
                    file=file,
                    file_path=str(destination),
                )

    def upload_thumbnail(self, file, file_path: str):
        """
        Creates a thumbnail for the file on disk and then uploads to the relevant team directory
        """
        save_path = self.get_thumbnail_path(file.team, file.name).with_suffix(".png")
        disk_path = str(self.resolve(save_path))

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
            self.resolve(path).mkdir(parents=True, exist_ok=True)
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
                with open(self.resolve(file_url), "rb") as fh:
                    buf = BytesIO(fh.read())
        except self.s3_errors + (FileNotFoundError, OSError) as e:
            if log:
                frappe.log_error("Drive: could not read file", e)
            frappe.throw("Could not find this file.", frappe.DoesNotExistError)

        return buf

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
        return Path(storage_key(get_home_folder(team)["file_url"])) / self.settings.thumbnail_prefix / (name + ".thumbnail")

    def get_thumbnail(self, team, name):
        return self.get_file(
            frappe._dict({"team": team, "file_url": str(self.get_thumbnail_path(team, name))}), log=False
        )

    def get_legacy_trash_path(self, entity):
        """Where items trashed before trash_path existed were put."""
        return Path(storage_key(get_home_folder(entity.team)["file_url"])) / ".trash" / entity.file_name

    def exists(self, team, path: str | Path) -> bool:
        if self.s3_enabled:
            try:
                self.conn.head_object(Bucket=self.get_bucket(team), Key=storage_key(path))
                return True
            except self.s3_errors:
                return False
        return self.resolve(path).exists()

    def get_unused_path(self, team, path: Path) -> Path:
        """Return `path`, or `name (n).ext` next to it if something is already there."""
        candidate, n = path, 1
        while self.exists(team, candidate):
            candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
            n += 1
        return candidate

    @_not_if_flat
    def rename(self, entity):
        if not entity.file_url or entity.mime_type == "frappe/slides":
            return
        new_path = self.get_disk_path(entity)
        return self.move(entity, new_path)

    @_not_if_flat
    def move_to_trash(self, entity) -> str | None:
        """
        Move a file or folder into the team's .trash folder, under a name that is not taken.
        Returns where it was put, or None if there was nothing to move.
        """
        if not entity.file_url or entity.mime_type in ["frappe/slides", "link"]:
            return None

        trash_path = self.get_unused_path(entity.team, self.get_legacy_trash_path(entity))
        try:
            self._move(entity.team, entity.file_url, trash_path)
        except self.s3_errors + (FileNotFoundError,):
            frappe.log_error(f"Moved {entity.name} to trash without it being on disk")
            return None
        return str(trash_path)

    @_not_if_flat
    def restore(self, entity, new_path: str | Path):
        """
        Move a file or folder from the trash to `new_path`.
        """
        trash_path = entity.trash_path
        if not trash_path:
            # Trashed before trash_path was stored
            trash_path = self.get_legacy_trash_path(entity)
            if not entity.file_url or not self.exists(entity.team, trash_path):
                return
        self.move(frappe._dict(file_url=trash_path, team=entity.team), new_path)

    @_not_if_flat
    def move(self, entity, new_path: str | Path):
        """
        Move a file or folder. Never replaces anything at `new_path`.
        """
        try:
            self._move(entity.team, entity.file_url, new_path)
        except self.s3_errors + (FileNotFoundError,):
            frappe.throw("This file doesn't exist on disk.")
        return new_path

    def _move(self, team, path: str | Path, new_path: str | Path):
        """
        Move bytes without replacing anything, and move them back if the transaction is rolled back,
        so that disk and database stay in step.
        """
        if storage_key(path) == storage_key(new_path):
            return
        if self.exists(team, new_path):
            frappe.throw(f"Could not move: '{storage_key(new_path)}' already exists.", FileExistsError)
        self._move_object(team, path, new_path)

        def undo():
            try:
                self._move_object(team, new_path, path)
            except Exception:
                frappe.log_error(f"Could not move {new_path} back to {path} after a rollback")

        frappe.db.after_rollback.add(undo)

    def _move_object(self, team, path: str | Path, new_path: str | Path):
        # Callers pass paths as either bare keys or stored file_urls
        if self.s3_enabled:
            bucket = self.get_bucket(team)
            source = storage_key(path)
            self.conn.copy_object(Bucket=bucket, CopySource={"Bucket": bucket, "Key": source}, Key=storage_key(new_path))
            self.conn.delete_object(Bucket=bucket, Key=source)
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
                self.conn.delete_object(Bucket=bucket, Key=storage_key(entity.file_url))
                if thumbnail_path:
                    self.conn.delete_object(Bucket=bucket, Key=str(thumbnail_path))
            except:
                pass
        else:
            try:
                self.resolve(entity.file_url).unlink()
                if thumbnail_path:
                    self.resolve(thumbnail_path).unlink()
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
