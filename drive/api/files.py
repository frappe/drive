import json
import re
import zipfile
from io import BytesIO
from pathlib import Path

import frappe
# import magic
import mimemapper
from pypika import Order
from werkzeug.utils import secure_filename, send_file
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

from drive.api.storage import storage_bar_data
from drive.utils import (
    create_drive_file,
    default_team,
    get_file_type,
    get_home_folder,
    update_file_size,
    get_new_file_name,
    validate_filename,
    get_upload_path,
    is_site_file,
    ATTACHMENT_CONTENT_DOCTYPE,
    STATUS_ACTIVE,
    STATUS_TRASHED,
)
from drive.utils.api import prettify_file
from drive.utils.files import FileManager, storage_key, get_s3_key, get_s3_url
from drive.utils.users import mark_as_viewed

from .permissions import get_teams, user_has_permission

FORBIDDEN_DOWNLOAD_TYPES = ["Folder", "Link", "Document", "Presentation"]


@frappe.whitelist(allow_guest=True)
@default_team
def upload_file(
    team: str,
    total_file_size: int = 0,
    file_modified: int = None,
    fullpath: str = None,
    parent: str = None,
    embed: int = 0,
):
    """
    Accept chunked file contents via a multipart upload.
    Store the file on disk, and insert a corresponding DriveFile doc.
    Works with normal uploads, and embeds.
    :return: DriveFile doc once the entire file has been uploaded
    """
    checks = frappe.get_hooks("validate_drive_upload")
    for check in checks:
        res = frappe.call(check, file=frappe.request.files["file"], team=team, parent=parent, embed=embed)
        if res is not None and res is not True:
            frappe.throw(res or "This upload was cancelled by a validation check.", TypeError)

    home_folder = get_home_folder(team)
    parent = parent or home_folder["name"]

    if not user_has_permission(parent, "upload"):
        frappe.throw("Ask the folder owner for upload access.", frappe.PermissionError)

    team = frappe.db.get_value("File", parent, "team")
    if fullpath:
        parent = ensure_path(team, fullpath, parent)

    # Support both chunked and non-chunked uploads
    if frappe.form_dict.chunk_index:
        current_chunk = int(frappe.form_dict.chunk_index)
        total_chunks = int(frappe.form_dict.total_chunk_count)
        offset = int(frappe.form_dict.chunk_byte_offset)
    else:
        offset = 0
        current_chunk = 0
        total_chunks = 1

    file = frappe.request.files["file"]
    file_name = get_new_file_name(file.filename, parent)
    upload_session = frappe.form_dict.uuid
    temp_path = get_upload_path(storage_key(home_folder["file_url"]), f"{upload_session}_{secure_filename(file_name)}")
    with temp_path.open("ab") as f:
        f.seek(offset)
        f.write(file.stream.read())
        if not f.tell() >= int(total_file_size) or current_chunk != total_chunks - 1:
            return

    # Validate that file size is matching
    file_size = temp_path.stat().st_size
    storage_data = storage_bar_data(team)
    if (storage_data["limit"] - storage_data["total_size"]) < file_size:
        frappe.throw("You're out of storage!", ValueError)

    mime_type = mimemapper.get_mime_type(str(temp_path), native_first=False)
    if mime_type is None:
        mime_type = magic.from_buffer(open(temp_path, "rb").read(2048), mime=True)

    file_type = get_file_type(mime_type)
    manager = FileManager()

    drive_file = create_drive_file(
        team,
        file_name,
        parent,
        file_type,
        lambda file: "/" + str(manager.get_disk_path(file, home_folder, embed)),
        mime_type,
        file_size,
        int(file_modified) / 1000 if file_modified else None,
    )

    # Upload and update parent folder size
    manager.upload_file(temp_path, drive_file, not embed)
    # Change path to be s3 compatible
    if manager.s3_enabled:
        drive_file.file_url = get_s3_url(get_s3_key(drive_file.file_url))
        drive_file.save()

    try:
        update_file_size(parent, file_size)
    except:
        # Find a cleaner way to handle folder sizes as multiple simultaneous uploads will break this
        pass

    frappe.publish_realtime("list-add", {"file": prettify_file(drive_file.as_dict())})

    return drive_file


@frappe.whitelist(allow_guest=True)
def get_thumbnail(entity_name: str):
    drive_file = frappe.get_cached_doc("File", entity_name)
    if not drive_file or drive_file.is_folder:
        return

    if not user_has_permission(drive_file, "read"):
        frappe.throw("No permission", frappe.PermissionError)

    thumbnail_data = None
    if frappe.cache().exists(entity_name):
        try:
            thumbnail_data = frappe.cache().get_value(entity_name)
        except:
            frappe.cache().delete_value(entity_name)
    if not thumbnail_data:
        manager = FileManager()
        try:
            if drive_file.file_type == "Markdown":
                with manager.get_file(drive_file) as f:
                    thumbnail_data = f.read()[:1000].decode("utf-8").replace("\n", "<br/>")
            elif drive_file.file_type == "Document":
                html = frappe.get_value("Writer Document", drive_file.content_docname, "html")
                thumbnail_data = html[:1000] if html else ""
            elif drive_file.mime_type == "frappe/slides":
                thumbnail_url = frappe.call(
                    "slides.slides.doctype.presentation.presentation.get_presentation_thumbnail",
                    presentation_name=drive_file.path,
                )
                if not thumbnail_url:
                    return ""
                frappe.local.response["type"] = "redirect"
                frappe.local.response["location"] = thumbnail_url
                return
            else:
                thumbnail = manager.get_thumbnail(drive_file.team, entity_name)
                thumbnail_data = BytesIO(thumbnail.read())
                thumbnail.close()
        except:
            return ""

    if thumbnail_data:
        frappe.cache().set_value(entity_name, thumbnail_data, expires_in_sec=60 * 60)

    if isinstance(thumbnail_data, BytesIO):
        response = Response(
            wrap_file(frappe.request.environ, thumbnail_data),
            direct_passthrough=True,
        )
        response.headers.set("Content-Type", "image/jpeg")
        response.headers.set("Content-Disposition", "inline", filename=entity_name)
        return response
    else:
        return thumbnail_data




@frappe.whitelist()
@default_team
def create_folder(team: str, file_name: str, parent: str | None = None):
    home_folder = get_home_folder(team)
    parent = parent or home_folder.name
    team = frappe.db.get_value("File", parent, "team")

    parent_doc = frappe.get_doc("File", parent)
    if not user_has_permission(parent_doc, "upload"):
        frappe.throw(
            "You don't have permissions for this.",
            frappe.PermissionError,
        )
    validate_filename(file_name, parent, "Folder", error=f"Folder '{file_name}' already exists.")

    manager = FileManager()
    path = manager.create_folder(
        frappe._dict(
            {
                "file_name": file_name,
                "team": team,
                "parent_path": Path(parent_doc.file_url or ""),
            }
        ),
        home_folder,
    )

    return create_drive_file(
        team,
        file_name,
        parent,
        "Folder",
        path,
    )


def ensure_path(team, fullpath, parent=None):
    """
    Walk through a folder path and ensure every part exists.

    :param team: Team ID
    :param fullpath: Path string, e.g. "foo/bar/baz"
    :param parent: Optional starting folder (defaults to home folder)
    :return: The name of the deepest folder
    """
    parts = Path(fullpath).parts
    current_parent = parent

    for folder in parts[:-1]:
        exists = frappe.db.get_value(
            "File",
            {
                "file_name": folder,
                "is_folder": 1,
                "status": STATUS_ACTIVE,
                "team": team,
                "folder": current_parent,
            },
            "name",
        )
        if not exists:
            # use the higher-level folder creation
            doc = create_folder(team, folder, parent=current_parent)
            current_parent = doc.name
        else:
            current_parent = exists
    return current_parent


@frappe.whitelist()
@default_team
def create_link(team: str, file_name: str, link: str, parent: str | None = None):
    home_folder = get_home_folder(team)
    parent = parent or home_folder.name

    if not user_has_permission(parent, "upload"):
        frappe.throw(
            "Cannot create link due to insufficient permissions.",
            frappe.PermissionError,
        )

    validate_filename(file_name, parent, "Link", error=f"Link '{file_name}' already exists.")

    drive_file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": file_name,
            "team": team,
            "file_url": link,
            "file_type": "Link",
            "file_modified": frappe.utils.now_datetime(),
            "folder": parent,
        }
    )
    drive_file.insert()

    return drive_file


@frappe.whitelist(allow_guest=True)
def create_auth_token(entity_name: str):
    if not user_has_permission(entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")
    token = frappe.get_doc(
        {
            "doctype": "Drive Token",
            "file": entity_name,
            "user": frappe.session.user,
            "expiry": frappe.utils.add_to_date(None, minutes=5),
        }
    ).insert(ignore_permissions=True)
    return token.name


@frappe.whitelist(allow_guest=True)
def get_file_content(entity_name: str, trigger_download: bool = False, token: str | None = None):
    """
    Central function to get files.
    """
    if token:
        # Single-use capability minted by create_auth_token, for cookieless
        # fetches (e.g. the Office Online preview).
        auth = frappe.db.get_value("Drive Token", token, ["file", "expiry"], as_dict=True)
        if not auth or auth.file != entity_name or frappe.utils.now_datetime() > auth.expiry:
            raise frappe.PermissionError("You do not have permission to view this file")
        frappe.delete_doc("Drive Token", token, ignore_permissions=True, force=True)
    elif not user_has_permission(entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    file = frappe.get_value(
        "File",
        {"name": entity_name},
        [
            "file_name",
            "file_type",
            "status",
            "file_url",
            "team",
        ],
        as_dict=1,
    )

    if not file or file.file_type in FORBIDDEN_DOWNLOAD_TYPES or file.status != STATUS_ACTIVE:
        frappe.throw("Not found", frappe.DoesNotExistError)

    if file.file_type == "Document" or is_site_file(file):
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = file.file_url if is_site_file(file) else ("/drive/w/" + file.name)
        return

    return get_file_internal(file, trigger_download)


def get_file_internal(file, trigger_download=0):
    if not trigger_download and file.file_type == "Video" and frappe.request.headers.get("Range"):
        return stream_file_content(file.name)

    manager = FileManager()
    return send_file(
        manager.get_file(file),
        as_attachment=trigger_download,
        conditional=True,
        max_age=3600,
        download_name=file.file_name,
        environ=frappe.request.environ,
    )


@frappe.whitelist(allow_guest=True)
def stream_file_content(entity_name: str):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param drive_entity: Drive Entity record object
    """
    range_header = frappe.request.headers.get("Range")
    if not range_header:
        return get_file_content(entity_name)
    entity = frappe.get_doc("File", entity_name)
    if not user_has_permission(entity, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    if is_site_file(entity):
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = entity.file_url
        return

    size = entity.file_size
    byte1, byte2 = 0, None

    m = re.search("(\d+)-(\d*)", range_header)
    g = m.groups()

    if g[0]:
        byte1 = int(g[0])
    if g[1]:
        byte2 = int(g[1])

    length = size - byte1

    max_length = 20 * 1024 * 1024  # 20 MB in bytes
    if length > max_length:
        length = max_length

    if byte2 is not None:
        length = byte2 - byte1

    manager = FileManager()
    data = None
    if manager.s3_enabled:
        data = manager.get_file(entity, f"bytes={byte1}-{byte1 + length - 1}")
    else:
        with manager.open_file(entity.file_url) as f:
            f.seek(byte1)
            data = f.read(length)

    res = Response(data, 206, mimetype=entity.mime_type, direct_passthrough=True)
    res.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(byte1, byte1 + length - 1, size))
    return res


class _ZipSink:
    """A non-seekable sink for `zipfile`. Because it exposes no `seek`/`tell`,
    zipfile falls back to streaming-friendly data descriptors, letting us yield
    archive bytes as they're produced instead of buffering the whole zip."""

    def __init__(self):
        self._chunks = bytearray()

    def write(self, data):
        self._chunks += data
        return len(data)

    def flush(self):
        pass

    def drain(self):
        chunk = bytes(self._chunks)
        del self._chunks[:]
        return chunk


def _iter_folder_files(entity_name, prefix=""):
    """Recursively yield (arcname, file) for downloadable files in a folder.

    Writer documents and links have no underlying blob, so they're skipped.
    """
    children = frappe.get_all(
        "File",
        filters={"folder": entity_name, "status": STATUS_ACTIVE},
        fields=["name", "file_name", "is_folder", "file_type", "file_url", "team"],
    )
    for child in children:
        arcname = f"{prefix}{child.file_name}"
        if child.is_folder:
            yield from _iter_folder_files(child.name, prefix=f"{arcname}/")
        elif child.file_type not in FORBIDDEN_DOWNLOAD_TYPES and child.file_url:
            yield arcname, child


def _collect_download_files(entity_names):
    """Expand the selected top-level entities into (arcname, file) pairs.

    Read permission is checked per top-level entity (Drive's ACL cascades to
    children); a single folder nests its contents under its own file name.
    """
    for name in entity_names:
        if not user_has_permission(name, "read"):
            raise frappe.PermissionError("You do not have permission to download this file")
        entity = frappe.get_value(
            "File",
            name,
            ["name", "file_name", "is_folder", "file_type", "file_url", "team"],
            as_dict=True,
        )
        if not entity:
            continue
        if entity.is_folder:
            yield from _iter_folder_files(entity.name, prefix=f"{entity.file_name}/")
        elif entity.file_type not in FORBIDDEN_DOWNLOAD_TYPES and entity.file_url:
            yield entity.file_name, entity


def _stream_zip(files):
    """Generator that yields a ZIP archive built one file at a time, so memory
    stays flat regardless of the total size."""
    manager = FileManager()
    sink = _ZipSink()
    with zipfile.ZipFile(sink, "w", zipfile.ZIP_STORED, allowZip64=True) as zf:
        for arcname, child in files:
            info = zipfile.ZipInfo(arcname)
            info.compress_type = zipfile.ZIP_STORED
            with zf.open(info, "w") as dest:
                source = manager.get_file(child)
                try:
                    while True:
                        block = source.read(4 * 1024 * 1024)
                        if not block:
                            break
                        dest.write(block)
                        data = sink.drain()
                        if data:
                            yield data
                finally:
                    if hasattr(source, "close"):
                        source.close()
            data = sink.drain()
            if data:
                yield data
    yield sink.drain()


@frappe.whitelist(allow_guest=True)
def download_folder(entities: str):
    """Stream a ZIP of one or more Drive entities (folders and/or files).

    Replaces the old client-side JSZip flow, which loaded every file into
    browser memory and hung on large folders. Here the server streams the
    archive a file at a time via chunked transfer.

    :param entities: JSON list of File names (the user's selection)
    """
    if isinstance(entities, str):
        entities = frappe.parse_json(entities)
    if not entities:
        frappe.throw("Nothing to download", ValueError)

    # Materialise the file list up front so a permission error surfaces as a
    # clean HTTP error instead of a corrupt, half-streamed zip.
    files = list(_collect_download_files(entities))
    if not files:
        frappe.throw("No downloadable files found", frappe.NotFound)

    if len(entities) == 1:
        title = frappe.get_value("File", entities[0], "file_name")
        zip_name = f"{title}.zip"
    else:
        zip_name = f"Drive Download {frappe.utils.now()}.zip"

    response = Response(_stream_zip(files), mimetype="application/zip", direct_passthrough=True)
    response.headers["Content-Disposition"] = f'attachment; filename="{secure_filename(zip_name)}"'
    return response


@frappe.whitelist()
def set_favourite(entities: list | None = None, clear_all: bool = False):
    """
    Favouite or unfavourite DriveEntities for specified user

    :param entities: List[dict] of document names and whether favorite
    :raises ValueError: If decoded entity_names is not a list
    """
    if clear_all:
        return frappe.db.delete("Drive Favourite", {"user": frappe.session.user})

    if not isinstance(entities, list):
        frappe.throw(f"Expected list but got {type(entities)}", ValueError)

    for entity in entities:
        existing_doc = frappe.db.exists(
            {
                "doctype": "Drive Favourite",
                "entity": entity["name"],
                "user": frappe.session.user,
            }
        )
        if not entity.get("is_favourite"):
            entity["is_favourite"] = not existing_doc

        if not isinstance(entity["is_favourite"], bool):
            entity["is_favourite"] = json.loads(entity["is_favourite"])

        if not entity["is_favourite"] and existing_doc:
            frappe.delete_doc("Drive Favourite", existing_doc)
        elif entity["is_favourite"] and not existing_doc:
            frappe.get_doc(
                {
                    "doctype": "Drive Favourite",
                    "entity": entity["name"],
                    "user": frappe.session.user,
                }
            ).insert()


@frappe.whitelist()
def remove_or_restore(entity_names: list[str] | str):
    """
    To move entities to or restore entities from the trash

    :param entity_names: List of document-names
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    manager = FileManager()

    def depth_zero_toggle_status(doc):
        if not user_has_permission(doc, "write"):
            raise frappe.PermissionError("You do not have permission to remove this file")
        if doc.status == STATUS_ACTIVE:
            flag = STATUS_TRASHED
            manager.move_to_trash(doc)
        else:
            storage_data = storage_bar_data(doc.team)
            if (storage_data["limit"] - storage_data["total_size"]) < doc.file_size:
                frappe.throw("You're out of storage!", ValueError)
            manager.restore(doc)
            flag = STATUS_ACTIVE

        doc.status = flag
        doc.file_modified = frappe.utils.now_datetime()
        # Only update parent folder size if parent exists (not root level)
        if doc.folder:
            folder_size = frappe.db.get_value("File", doc.folder, "file_size") or 0
            frappe.db.set_value(
                "File",
                doc.folder,
                "file_size",
                folder_size + doc.file_size * (1 if flag == STATUS_ACTIVE else -1),
            )

        doc.save()

    for entity in entity_names:
        depth_zero_toggle_status(frappe.get_doc("File", entity))


@frappe.whitelist()
def delete_entities(entity_names: list[str] | None = None, clear_all: bool = False):
    if clear_all:
        entity_names = frappe.db.get_list("File", {"status": STATUS_TRASHED, "owner": frappe.session.user}, pluck="name")
    elif isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    elif not isinstance(entity_names, list) or not entity_names:
        frappe.throw(f"Expected non-empty list but got {type(entity_names)}", ValueError)

    for entity in entity_names:
        frappe.get_doc("File", entity).permanent_delete()


@frappe.whitelist()
def rename(entity_name: str, new_title: str):
    drive_file = frappe.get_doc("File", entity_name)
    return drive_file.rename(new_title)


# Will be replaced after new JS composables refactor
@frappe.whitelist()
def update_access(entity_name: str, method: str, **kwargs):
    drive_file = frappe.get_doc("File", entity_name)
    kwargs.pop("cmd")
    if not drive_file:
        frappe.throw("Entity does not exist", ValueError)
    if method == "share":
        return drive_file.share(**kwargs)
    elif method == "unshare":
        return drive_file.unshare(user=kwargs.get("user"))


@frappe.whitelist()
def remove_recents(entity_names: list[str] | None = [], clear_all: bool = False):
    """
    Clear recent DriveEntities for specified user

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """
    if clear_all:
        return frappe.db.delete("Drive Entity Log", {"user": frappe.session.user})
    elif not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)

    for entity in entity_names:
        existing_doc = frappe.db.exists(
            {
                "doctype": "Drive Entity Log",
                "entity_name": entity,
                "user": frappe.session.user,
            }
        )
        if existing_doc:
            frappe.delete_doc("Drive Entity Log", existing_doc)


@frappe.whitelist()
@default_team
def does_entity_exist(name: str | None = None, folder: str | None = None, team: str | None = None):
    if not folder:
        home_folder = get_home_folder(team)
        folder = home_folder.name
    result = frappe.db.exists("File", {"folder": folder, "file_name": name})
    return result


@frappe.whitelist()
def get_new_title(title: str, parent_name: str, folder: bool = False):
    return get_new_file_name(title, parent_name, folder)


@frappe.whitelist()
@default_team
def move(entity_names: list[str], new_parent: str | None = None, team: str | None = None):
    """
    Move file or folder to the new parent folder

    :param new_parent: Document-name of the new parent folder. Defaults to the user directory
    :raises NotADirectoryError: If the new_parent is not a folder, or does not exist
    :raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
    :return: DriveEntity doc once file is moved
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not entity_names or not isinstance(entity_names, list):
        frappe.throw(f"Expected a non-empty list but got {type(entity_names)}", ValueError)

    for entity in entity_names:
        doc = frappe.get_doc("File", entity)
        res = doc.move(new_parent, team)

    if not res["folder"]:
        # Drive Team's display field is `title` (not `file_name`).
        title, personal = frappe.db.get_value("Drive Team", res["team"], ["title", "personal"])
        res["file_name"] = "Home" if personal else title

    return res


@frappe.whitelist()
def search(query: str):
    """
    Basic search implementation
    """
    text = " ".join(k + "*" for k in query.split())
    teams = get_teams()
    try:
        result = frappe.db.sql(
            """
        SELECT  `tabFile`.name,
                `tabFile`.file_name,
                `tabFile`.file_type,
                `tabFile`.content_doctype,
                `tabFile`.content_docname,
                `tabUser`.name AS user_name,
                `tabUser`.user_image,
                `tabUser`.full_name
        FROM `tabFile`
        LEFT JOIN `tabUser` ON `tabFile`.`owner` = `tabUser`.`name`
        WHERE `tabFile`.team IN %(teams)s
            AND `tabFile`.`status` = %(status)s
            AND COALESCE(`tabFile`.`folder`, '') <> ''
            AND MATCH(`tabFile`.file_name) AGAINST (%(text)s IN BOOLEAN MODE)
        GROUP BY `tabFile`.`name`
        """,
            values={"teams": teams, "text": text, "status": STATUS_ACTIVE},
            as_dict=1,
        )
        return result
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Frappe Drive Search Error")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def translate_old_name(old_name: str):
    return frappe.get_value("File", {"old_name": old_name}, "name")


@frappe.whitelist(allow_guest=True)
def get_entity_type(entity_name: str):
    if not user_has_permission(entity_name, "read"):
        frappe.throw("You do not have permission to view this file.", frappe.PermissionError)

    entity = frappe.db.get_value(
        "File",
        {"status": STATUS_ACTIVE, "name": entity_name},
        ["name", "file_type"],
        as_dict=1,
    )
    if entity.file_type == "Folder":
        entity["type"] = "folder"
    else:
        entity["type"] = "file"
    return entity


@frappe.whitelist()
def get_root_folder(team: str):
    if team not in get_teams():
        frappe.throw("You can't check the home folder of a team you don't belong to.", frappe.PermissionError)
    return get_home_folder(team)


@frappe.whitelist(allow_guest=True)
def redirect_to_original(file_id: str):
    """
    Redirect Drive attachments to original files
    """
    file = frappe.get_cached_doc("File", file_id)
    if not user_has_permission(file_id, "read"):
        frappe.throw("You do not have permission to view this file.", frappe.PermissionError)
    if not file.content_doctype == ATTACHMENT_CONTENT_DOCTYPE:
        frappe.throw("This is not an attachment", ValueError)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/drive/g/" + file.content_docname


@frappe.whitelist()
def track_visit(entity_name: str):
    entity = frappe.get_doc("File", entity_name)
    mark_as_viewed(entity)


@frappe.whitelist()
def get_docs_attached_to(file_name: str):
    file = frappe.get_doc("File", file_name)
    return frappe.get_list(
        "File",
        filters={"attached_to_doctype": ["is", "set"], "file_url": file.file_url},
        fields=["attached_to_doctype", "attached_to_name"],
    )
