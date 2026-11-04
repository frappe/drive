import contextlib
import json
import os
import re
import shutil
import time
import uuid
import zipfile
from pathlib import Path

import frappe
from frappe.utils import get_site_path

from drive.utils.files import FileManager

from .permissions import user_has_permission

DOWNLOAD_ROOT = "private/files/.downloads"
DOWNLOAD_TTL_SECONDS = 24 * 60 * 60  # stale zips are purged after 24h

# Extensions that actually benefit from DEFLATE (plain text). Everything else
# (xlsx, pdf, jpg, png, mp4, docx, zip, ...) is already compressed, so zipping
# it just burns CPU with no size win.
COMPRESSIBLE_SUFFIXES = {
    "txt",
    "md",
    "log",
    "json",
    "csv",
    "tsv",
    "xml",
    "html",
    "htm",
    "css",
    "js",
    "py",
    "ini",
    "conf",
    "yaml",
    "yml",
}


def _compress_type(title: str) -> int:
    suffix = Path(title).suffix.lower().lstrip(".")
    return zipfile.ZIP_DEFLATED if suffix in COMPRESSIBLE_SUFFIXES else zipfile.ZIP_STORED


def _download_dir() -> Path:
    root = Path(get_site_path("private/files")).resolve()
    configured = Path(get_site_path(DOWNLOAD_ROOT))
    directory = configured.resolve()
    if configured.is_symlink() or directory == root or not directory.is_relative_to(root):
        frappe.throw("Invalid download storage.", frappe.PermissionError)
    return directory


def _artifact_path(download_id: str, suffix: str) -> Path:
    if not isinstance(download_id, str) or not re.fullmatch(r"[0-9a-f]{32}", download_id):
        frappe.throw("Invalid download id.", frappe.ValidationError)
    root = _download_dir()
    path = root / f"{download_id}.{suffix}"
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        frappe.throw("Invalid download storage.", frappe.PermissionError)
    return path


def _status_path(download_id: str) -> Path:
    return _artifact_path(download_id, "status")


def _zip_path(download_id: str) -> Path:
    return _artifact_path(download_id, "zip")


def _purge_stale():
    """Delete download artifacts older than TTL so failed/abandoned jobs don't leak disk."""
    d = _download_dir()
    if not d.exists():
        return
    cutoff = frappe.utils.now_datetime().timestamp() - DOWNLOAD_TTL_SECONDS
    for entry in d.glob("*"):
        try:
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


def _set_status(download_id: str, status: dict):
    _download_dir().mkdir(parents=True, exist_ok=True)
    _status_path(download_id).write_text(json.dumps(status))
    frappe.db.commit()


@frappe.whitelist(methods=["POST"])
def download_zip(team, entity_names, filename=None):
    """
    Enqueue a background job that builds a zip of the given entities on the
    server. The frontend polls `download_status` and then streams the result
    through `get_download_zip`. Keeps heavy zipping off the browser so large
    folders don't exhaust tab memory (RangeError) or trip fetch timeouts.

    :param team: Drive team name
    :param entity_names: JSON list of top-level Drive File names
    :param filename: desired download name (without .zip) for the response
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list) or not entity_names:
        frappe.throw("No files selected to download.", frappe.ValidationError)

    for name in entity_names:
        entity = frappe.get_value("Drive File", name, ["team", "is_active", "is_group", "document"], as_dict=True)
        if not entity:
            frappe.throw(f"Not found ({name})", frappe.NotFound)
        if not user_has_permission(name, "read"):
            frappe.throw("You don't have access.", frappe.PermissionError)

    _purge_stale()
    download_id = uuid.uuid4().hex
    zip_name = (filename or "Drive Download") + ".zip"

    _set_status(
        download_id,
        {"status": "queued", "filename": zip_name, "skipped": 0, "message": "", "user": frappe.session.user},
    )

    frappe.enqueue(
        "drive.api.download.build_download_zip",
        queue="long",
        timeout=1800,
        job_id=f"drive_zip_{download_id}",
        team=team,
        entity_names=entity_names,
        download_id=download_id,
        zip_name=zip_name,
    )

    return {"download_id": download_id, "filename": zip_name}


def build_download_zip(team, entity_names, download_id, zip_name=None):
    """
    Background job: walk the entity tree server-side and stream every file
    straight into a zip on disk. Files are copied in chunks so the worker never
    holds an entire folder in memory. Link entities are skipped and counted.
    Compression is per-file: STORE for already-compressed formats (near disk
    speed), DEFLATE only for plain-text types that actually shrink.
    """
    filename = zip_name or ""
    _set_status(
        download_id,
        {"status": "running", "filename": filename, "skipped": 0, "message": "", "user": frappe.session.user},
    )
    manager = FileManager()
    skipped = 0
    total = 0
    for name in entity_names:
        _, files = _estimate_entity(name)
        total += files
    processed = 0
    last_status = 0.0
    tmp_path = _zip_path(download_id).with_suffix(".zip.tmp")
    _download_dir().mkdir(parents=True, exist_ok=True)

    def _bump_progress():
        nonlocal processed, last_status
        processed += 1
        now = time.monotonic()
        if now - last_status < 0.5:
            return
        last_status = now
        _set_status(
            download_id,
            {
                "status": "running",
                "filename": filename,
                "skipped": skipped,
                "message": "",
                "user": frappe.session.user,
                "processed": processed,
                "total": total,
            },
        )

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_STORED) as zf:
            for name in entity_names:
                skipped += _zip_entity(manager, name, zf, parent_path=Path(), on_file=_bump_progress)
        tmp_path.replace(_zip_path(download_id))
        _set_status(
            download_id,
            {
                "status": "ready",
                "filename": filename or _zip_path(download_id).name,
                "skipped": skipped,
                "message": "",
                "user": frappe.session.user,
                "processed": total,
                "total": total,
            },
        )
    except Exception as e:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        frappe.log_error(message=f"Drive download {download_id} failed: {e}", title="Drive Download Failed")
        _set_status(
            download_id,
            {"status": "error", "filename": "", "skipped": skipped, "message": str(e), "user": frappe.session.user},
        )
        raise


def _zip_entity(manager: FileManager, entity_name: str, zf: zipfile.ZipFile, parent_path: Path, on_file=None, _depth=0) -> int:
    """Add one entity (file, folder or doc) to the zip. Returns count of skipped links."""
    if _depth > 100:
        frappe.throw("Invalid folder tree.", frappe.ValidationError)
    if not user_has_permission(entity_name, "read"):
        frappe.throw("You don't have access.", frappe.PermissionError)
    entity = frappe.get_value(
        "Drive File",
        entity_name,
        ["name", "title", "is_group", "is_link", "path", "parent_entity", "mime_type", "document", "team", "is_active", "file_size"],
        as_dict=True,
    )
    if not entity or entity.is_active != 1:
        return 1
    if not entity.title or entity.title in (".", "..") or any(c in entity.title for c in ("/", "\\", "\0")):
        frappe.throw("Invalid file name in download.", frappe.ValidationError)
    arc_parent = parent_path / entity.title
    if entity.is_group:
        children = frappe.get_all(
            "Drive File",
            filters={"parent_entity": entity.name, "is_active": 1},
            fields=["name"],
            order_by="title asc",
        )
        for child in children:
            _zip_entity(manager, child.name, zf, arc_parent, on_file=on_file, _depth=_depth + 1)
        return 0
    if entity.is_link:
        return 1

    if entity.mime_type == "frappe_doc":
        content = frappe.get_value("Drive Document", entity.document, "content") or ""
        info = zipfile.ZipInfo(str(arc_parent.with_suffix(".html")))
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, content)
        if on_file:
            on_file()
        return 0

    info = zipfile.ZipInfo(str(arc_parent))
    info.compress_type = _compress_type(entity.title)
    force_zip64 = bool(entity.file_size and entity.file_size > zipfile.ZIP64_LIMIT)
    with _open_entity_file(manager, entity) as src:
        with zf.open(info, "w", force_zip64=force_zip64) as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
    if on_file:
        on_file()
    return 0


def _open_entity_file(manager: FileManager, entity):
    """Stream through FileManager's storage boundary checks for both disk and S3."""
    return manager.open_file(entity.path) if not manager.s3_enabled else contextlib.closing(manager.get_file(entity))


@frappe.whitelist()
def estimate_download(team, entity_names):
    """
    Cheap DB-only estimate of a download: total byte size and file count for the
    given entities (recursively). The frontend uses this to pick the fast
    client-side zip for small selections and the server-side enqueue flow for
    heavy ones. Links are excluded; docs count as a file with 0 bytes (their
    content lives in the DB, not on disk).
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)

    total_size = 0
    count = 0
    for name in entity_names:
        size, files = _estimate_entity(name)
        total_size += size
        count += files

    return {"total_size": total_size, "count": count}


def _estimate_entity(entity_name: str, _depth: int = 0):
    if _depth > 100:
        return 0, 0
    if not user_has_permission(entity_name, "read"):
        frappe.throw("You don't have access.", frappe.PermissionError)
    entity = frappe.get_value(
        "Drive File",
        entity_name,
        ["name", "is_group", "is_link", "file_size", "mime_type"],
        as_dict=True,
    )
    if not entity or entity.is_link:
        return 0, 0
    if entity.is_group:
        total_size = 0
        count = 0
        children = frappe.get_all(
            "Drive File",
            filters={"parent_entity": entity.name, "is_active": 1},
            fields=["name"],
        )
        for child in children:
            size, files = _estimate_entity(child.name, _depth + 1)
            total_size += size
            count += files
        return total_size, count
    if entity.mime_type == "frappe_doc":
        return 0, 1
    return entity.file_size or 0, 1


@frappe.whitelist()
def get_doc_content(entity_name):
    """Return the raw editor content of a Drive Document for client-side zips."""
    if not user_has_permission(entity_name, "read"):
        frappe.throw("You don't have access.", frappe.PermissionError)
    doc = frappe.get_value("Drive File", entity_name, "document")
    if not doc:
        frappe.throw("Not found", frappe.NotFound)
    return frappe.get_value("Drive Document", doc, "content") or ""


@frappe.whitelist()
def download_status(download_id):
    """Return the build status for a download id: queued/running/ready/error."""
    status_file = _status_path(download_id)
    if status_file.is_file():
        try:
            status = json.loads(status_file.read_text())
        except (json.JSONDecodeError, OSError):
            frappe.throw("Download status is unreadable.", frappe.PermissionError)
    else:
        frappe.throw("Download was not found.", frappe.NotFound)

    if not isinstance(status, dict) or status.get("user") != frappe.session.user:
        frappe.throw("You don't have access.", frappe.PermissionError)

    if status.get("status") == "ready" and not _zip_path(download_id).is_file():
        status = {"status": "error", "message": "Download file is missing."}
    return status


@frappe.whitelist()
def get_download_zip(download_id):
    """Stream the finished zip to the browser and delete it once sent."""
    from werkzeug.utils import send_file

    status = download_status(download_id)
    if status.get("status") != "ready":
        frappe.throw("Download is not ready.", frappe.NotFound)
    zip_path = _zip_path(download_id)
    if not zip_path.is_file():
        frappe.throw("Download is not ready.", frappe.NotFound)

    download_name = status.get("filename") or zip_path.name

    # The file is removed as soon as the response has been streamed out.
    response = send_file(
        _SelfDeletingFile(zip_path),
        mimetype="application/zip",
        as_attachment=True,
        conditional=False,
        max_age=0,
        download_name=download_name,
        environ=frappe.local.request.environ,
    )
    # send_file can't size a file object, so it would fall back to chunked
    # transfer. Browsers need Content-Length for large (>2GB) downloads to
    # show progress and to reliably finish the transfer.
    response.headers["Content-Length"] = str(zip_path.stat().st_size)
    return response


class _SelfDeletingFile:
    """Wraps an open file so it is deleted from disk once closed (i.e. after the
    WSGI server has finished streaming the response)."""

    def __init__(self, path: Path):
        self._path = path
        self._fh = open(path, "rb")

    def __getattr__(self, item):
        return getattr(self._fh, item)

    def close(self):
        try:
            self._fh.close()
        finally:
            try:
                self._path.unlink()
            except OSError:
                pass
