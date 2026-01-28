import json
import os
import re
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

import frappe
import html2text
import jwt
import magic
import mimemapper
from pypika import Order
from werkzeug.utils import secure_filename, send_file
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

from drive.api.notifications import notify_mentions
from drive.api.storage import storage_bar_data
from drive.utils import (
    create_drive_file,
    default_team,
    extract_mentions,
    get_file_type,
    get_home_folder,
    update_clients,
    strip_comment_spans,
    update_file_size,
    get_default_team,
)
from drive.utils.api import prettify_file
from drive.utils.files import FileManager

from .permissions import get_teams, user_has_permission


@frappe.whitelist(allow_guest=True)
def upload_embed(doc):
    doc = frappe.get_doc("Drive File", doc)
    file = frappe.request.files["file"]
    file.filename = "Embed - " + doc.name
    embed = upload_file(doc.team, parent=doc.name, embed=1)
    return {
        "file_url": f"/api/method/drive.api.embed.get_file_content?embed_name={embed.name}&parent_entity_name={doc.name}"
    }


@frappe.whitelist(allow_guest=True)
@default_team
def upload_file(
    team,
    total_file_size=0,
    last_modified=None,
    fullpath=None,
    parent=None,
    embed=0,
    transfer=0,
):
    """
    Accept chunked file contents via a multipart upload.
    Store the file on disk, and insert a corresponding DriveFile doc.
    Works with normal uploads, transfers, and embeds.
    :return: DriveFile doc once the entire file has been uploaded
    """
    checks = frappe.get_hooks("validate_drive_upload")
    for check in checks:
        res = frappe.call(check, file=frappe.request.files["file"], team=team, parent=parent, embed=embed)
        if res is not None and res is not True:
            frappe.throw(res or "This upload was cancelled by a validation check.", TypeError)

    home_folder = get_home_folder(team)
    parent = parent or home_folder["name"]
    embed = int(embed)

    # Get again for non-root folders
    if not embed and not user_has_permission(parent, "upload"):
        frappe.throw("Ask the folder owner for upload access.", frappe.PermissionError)

    team = frappe.db.get_value("Drive File", parent, "team")
    if fullpath:
        parent = ensure_path(team, fullpath, parent)

    # Support non-chunked uploads too
    if frappe.form_dict.chunk_index:
        current_chunk = int(frappe.form_dict.chunk_index)
        total_chunks = int(frappe.form_dict.total_chunk_count)
        offset = int(frappe.form_dict.chunk_byte_offset)
    else:
        offset = 0
        current_chunk = 0
        total_chunks = 1

    file = frappe.request.files["file"]
    title = get_new_title(file.filename, parent) if not transfer else file.filename
    upload_session = frappe.form_dict.uuid
    temp_path = get_upload_path(home_folder["path"], f"{upload_session}_{secure_filename(title)}")
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

    manager = FileManager()

    # Create DB record
    if transfer:
        entity = frappe.get_doc({"doctype": "Drive Transfer", "title": title, "file_size": file_size})
        entity.insert()
        entity.path = str(
            Path(home_folder["path"]) / (entity.name if manager.flat else Path(".transfers") / entity.title)
        )
        entity.save()
        drive_file = frappe._dict(**entity.as_dict(), team=team, parent=parent)
    else:
        drive_file = create_drive_file(
            team,
            title,
            parent,
            mime_type,
            lambda entity: manager.get_disk_path(entity, home_folder, embed),
            file_size,
            int(last_modified) / 1000 if last_modified else None,
        )

    # Upload and update parent folder size
    manager.upload_file(temp_path, drive_file, not embed and not transfer)

    try:
        update_clients(drive_file.name, drive_file.team, "upload")
        update_file_size(parent, file_size)
    except:
        # Find a cleaner way to handle folder sizes as multiple simultaneous uploads will break this
        pass

    if transfer:
        frappe.publish_realtime("transfer-add", {"file": drive_file})
    elif not embed:
        frappe.publish_realtime("list-add", {"file": prettify_file(drive_file.as_dict())})

    return drive_file


@frappe.whitelist(allow_guest=True)
def get_thumbnail(entity_name):
    drive_file = frappe.get_value(
        "Drive File",
        entity_name,
        [
            "is_group",
            "path",
            "title",
            "mime_type",
            "file_size",
            "owner",
            "team",
            "document",
            "name",
        ],
        as_dict=1,
    )
    if not drive_file or drive_file.is_group or drive_file.is_link:
        return
    if user_has_permission(drive_file, "read") is False:
        return

    thumbnail_data = None
    if frappe.cache().exists(entity_name):
        try:
            thumbnail_data = frappe.cache().get_value(entity_name)
        except:
            frappe.cache().delete_value(entity_name)
    if not thumbnail_data:
        manager = FileManager()
        try:
            if drive_file.mime_type.startswith("text"):
                with manager.get_file(drive_file) as f:
                    thumbnail_data = f.read()[:1000].decode("utf-8").replace("\n", "<br/>")
            elif drive_file.mime_type == "frappe_doc":
                html = frappe.get_value("Drive Document", drive_file.document, "raw_content")
                thumbnail_data = html[:1000] if html else ""
            elif drive_file.mime_type == "frappe/slides":
                # Use this until the thumbnail method is whitelisted
                thumbnails = frappe.call(
                    "slides.slides.doctype.presentation.presentation.get_slide_thumbnails",
                    presentation=drive_file.path,
                )
                frappe.local.response["type"] = "redirect"
                frappe.local.response["location"] = thumbnails[0]
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
def create_presentation(team, title=None, parent=None):
    home_directory = get_home_folder(team)
    parent = parent or home_directory.name
    team = frappe.db.get_value("Drive File", parent, "team")
    if not user_has_permission(parent, "upload"):
        frappe.throw(
            "Cannot access folder due to insufficient permissions",
            frappe.PermissionError,
        )
    try:
        r = frappe.call(
            "slides.slides.doctype.presentation.presentation.create_presentation",
            title=title,
            theme="1mjgj61m8j",
        )
    except BaseException as e:
        print("Couldn't create", e)
    entity = create_drive_file(
        team,
        title,
        parent,
        "frappe/slides",
        lambda _: r.name,
    )
    return entity


@frappe.whitelist()
@default_team
def create_document_entity(team, title=None, parent=None):
    home_directory = get_home_folder(team)
    parent = parent or home_directory.name
    parent_doc = frappe.get_cached_doc("Drive File", parent)
    team = frappe.db.get_value("Drive File", parent, "team")
    if not title:
        title = get_new_title("Untitled Document", parent)

    if not user_has_permission(parent, "upload"):
        frappe.throw(
            "Cannot access folder due to insufficient permissions",
            frappe.PermissionError,
        )
    drive_doc = frappe.new_doc("Drive Document")
    drive_doc.title = title
    drive_doc.settings = '{"collab": true}'
    drive_doc.save()

    manager = FileManager()
    path = manager.create_folder(
        frappe._dict(
            {
                "title": title,
                "parent_path": Path(parent_doc.path or ""),
                "team": team,
                "parent_entity": parent_doc.name,
            }
        ),
        home_directory,
    )
    manager.create_folder(
        frappe._dict(
            {
                "title": ".embeds",
                "team": team,
                "parent_path": path,
            }
        ),
        home_directory,
    )

    entity = create_drive_file(
        team,
        title,
        parent,
        "frappe_doc",
        lambda _: path,
        document=drive_doc.name,
    )
    return entity


def get_upload_path(team_path, file_name):
    uploads_path = Path(frappe.get_site_path("private/files"), team_path, ".uploads")
    if not os.path.exists(uploads_path):
        uploads_path = Path(frappe.get_site_path("private/files"), team_path, ".uploads")
        uploads_path.mkdir()
    return uploads_path / file_name


@frappe.whitelist()
@default_team
def create_folder(team, title, parent=None):
    """
    Create a new folder.

    :param title: Folder name
    :param parent: Document-name of the parent folder. Defaults to the user directory
    :raises PermissionError: If the user does not have write access to the specified parent folder
    :raises FileExistsError: If a folder with the same name already exists in the specified parent folder
    :return: DriveEntity doc of the new folder
    """
    home_folder = get_home_folder(team)
    parent = parent or home_folder.name
    team = frappe.db.get_value("Drive File", parent, "team")

    parent_doc = frappe.get_doc("Drive File", parent)
    if not user_has_permission(parent_doc, "upload"):
        frappe.throw(
            "You don't have permissions for this.",
            frappe.PermissionError,
        )
    entity_exists = frappe.db.exists(
        {
            "doctype": "Drive File",
            "parent_entity": parent,
            "is_group": 1,
            "title": title,
            "is_active": 1,
        }
    )

    if entity_exists:
        suggested_name = get_new_title(title, parent, folder=True)
        frappe.throw(
            f"Folder '{title}' already exists.\n Suggested: {suggested_name}",
            FileExistsError,
        )

    manager = FileManager()
    path = manager.create_folder(
        frappe._dict(
            {
                "title": title,
                "team": team,
                "parent_path": Path(parent_doc.path or ""),
            }
        ),
        home_folder,
    )

    drive_file = create_drive_file(
        team,
        title,
        parent,
        "folder",
        lambda _: path,
        is_group=True,
    )

    return drive_file


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
            "Drive File",
            {
                "title": folder,
                "is_group": 1,
                "is_active": 1,
                "team": team,
                "parent_entity": current_parent,
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
def create_link(team, title, link, parent=None):
    home_folder = get_home_folder(team)
    parent = parent or home_folder.name

    if not user_has_permission(parent, "upload"):
        frappe.throw(
            "Cannot create link due to insufficient permissions.",
            frappe.PermissionError,
        )
    entity_exists = frappe.db.exists(
        {
            "doctype": "Drive File",
            "parent_entity": parent,
            "is_group": 1,
            "title": title,
            "is_active": 1,
        }
    )

    if entity_exists:
        suggested_name = get_new_title(title, parent, folder=True)
        frappe.throw(
            f"File '{title}' already exists.\n Suggested: {suggested_name}",
            FileExistsError,
        )

    drive_file = frappe.get_doc(
        {
            "doctype": "Drive File",
            "title": title,
            "team": team,
            "path": link,
            "is_link": 1,
            "mime_type": "link/unknown",
            "_modified": frappe.utils.now_datetime(),
            "parent_entity": parent,
        }
    )
    drive_file.insert()

    return drive_file


@frappe.whitelist()
def edit_file_content(entity_name, client=None):
    # TBD: notify other clients of the update
    entity = frappe.get_doc("Drive File", entity_name)
    if not user_has_permission(entity, "write"):
        frappe.throw("You cannot edit this file", frappe.PermissionError)

    file = frappe.request.files["file"]
    home_folder = get_home_folder(entity.team)
    temp_path = get_upload_path(home_folder["path"], f"editing_{secure_filename(entity.title)}")
    with temp_path.open("ab") as f:
        f.write(file.stream.read())
    manager = FileManager()
    manager.delete_file(entity)
    manager.upload_file(temp_path, entity)
    entity._modified = frappe.utils.now_datetime()
    frappe.publish_realtime("list-update", {"file": prettify_file(entity.as_dict())})
    entity.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def save_doc(entity_name, doc_name=None, content=None, yjs=None, comment=False):
    # SECURITY: commenting also gives edit access in collab documents
    can_write = (
        user_has_permission(entity_name, "write")
        if not yjs
        else user_has_permission(entity_name, "comment" if comment else "write")
    )
    if comment and not can_write:
        old_content = frappe.db.get_value("Drive Document", doc_name, "raw_content")
        if not strip_comment_spans(old_content) == strip_comment_spans(content):
            raise frappe.PermissionError("You cannot edit file while commenting.")
        return frappe.db.set_value("Drive Document", doc_name, "raw_content", content)
    elif not can_write:
        raise frappe.PermissionError("You do not have permission to edit this file")

    if doc_name:
        try:
            if content:
                frappe.db.set_value("Drive Document", doc_name, "raw_content", content)
            if yjs:
                frappe.db.set_value("Drive Document", doc_name, "content", yjs)
                file = frappe.get_doc("Drive File", entity_name)
                file._modified = frappe.utils.now()
                file.file_size = len(yjs.encode("utf-8"))
                file.save(ignore_permissions=True)
        except (frappe.exceptions.QueryDeadlockError, frappe.exceptions.TimestampMismatchError):
            if yjs:
                # Pass if there's a deadlock, as CRDT is supposed to take care of it.
                frappe.log_error(f"There was a collision, not storing data - {entity_name}, {frappe.session.user}")
            else:
                frappe.throw("This schema doesn't support collaboration - you will likely lose data.")
    else:
        # Text based files
        # BROKEN - should reparse markdown files.
        h = html2text.HTML2Text()
        h.body_width = 0
        md_content = h.handle(content)
        path = frappe.db.get_value("Drive File", entity_name, "path")
        FileManager().write_file(path, md_content)

    if not yjs:
        file = frappe.get_doc("Drive File", entity_name)
        file._modified = frappe.utils.now()
        if content:
            file.file_size = len(content.encode("utf-8"))

        file.save()

    if content:
        mentions = extract_mentions(content)
        if mentions:
            frappe.enqueue(
                notify_mentions,
                job_id=f"doc_{entity_name}",
                now=True,
                deduplicate=True,
                entity_name=entity_name,
                mentions=mentions,
            )


@frappe.whitelist(allow_guest=True)
def create_auth_token(entity_name):
    if not user_has_permission(entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")
    settings = frappe.get_single("Drive Disk Settings")
    key = settings.get_password("jwt_key", raise_exception=False)
    return jwt.encode(
        {"name": entity_name, "expiry": (frappe.utils.now_datetime() + timedelta(minutes=1)).timestamp()},
        key=key,
    )


@frappe.whitelist(allow_guest=True)
def get_file_content(entity_name, trigger_download=0, jwt_token=None, transfer=False):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param trigger_download: 1 to trigger the "Save As" dialog. Defaults to 0
    :type trigger_download: int
    :raises ValueError: If the DriveEntity doc does not exist or is not a file
    :raises PermissionError: If the current user does not have permission to read the file
    :raises FileLockedError: If the file has been writer-locked

    JWT tokens are a vulnerability - if used, they bypass all permissions and give the file.
    Only the file name and secret token is needed to get access to all files.

    A more secure way would be a DB-stored auth token that can only be created by someone with read access.
    """
    if jwt_token:
        settings = frappe.get_single("Drive Disk Settings")
        auth = jwt.decode(jwt_token, key=settings.get_password("jwt_key"), algorithms=["HS256"])
        if frappe.utils.now_datetime().timestamp() > auth["expiry"] or auth["name"] != entity_name:
            raise frappe.PermissionError("You do not have permission to view this file")
    elif not user_has_permission(entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    trigger_download = int(trigger_download)
    if transfer:
        transfer = frappe.get_doc("Drive Transfer", entity_name)
        drive_file = frappe._dict(**transfer.as_dict(), team=get_default_team())
    else:
        drive_file = frappe.get_value(
            "Drive File",
            {"name": entity_name},
            [
                "is_group",
                "team",
                "is_link",
                "path",
                "title",
                "mime_type",
                "is_active",
                "document",
            ],
            as_dict=1,
        )
    if not drive_file or drive_file.is_group or drive_file.is_link or (not transfer and drive_file.is_active != 1):
        frappe.throw("Not found", frappe.NotFound)

    return get_file_internal(drive_file, trigger_download)


def get_file_internal(file, trigger_download=0):
    if (
        not trigger_download
        and get_file_type(file.as_dict() if file.as_dict else dict(file)) == "Video"
        and frappe.request.headers.get("Range")
    ):
        return stream_file_content(file.name)
    if file.document:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/drive/w/" + file.name
        return
    else:
        manager = FileManager()
        return send_file(
            manager.get_file(file),
            mimetype=file.mime_type,
            as_attachment=trigger_download,
            conditional=True,
            max_age=3600,
            download_name=file.title,
            environ=frappe.request.environ,
        )


@frappe.whitelist(allow_guest=True)
def stream_file_content(entity_name):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param drive_entity: Drive Entity record object
    """
    range_header = frappe.request.headers.get("Range")
    entity = frappe.get_doc("Drive File", entity_name)
    if not user_has_permission(entity, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")
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
        with manager.open_file(entity.path) as f:
            f.seek(byte1)
            data = f.read(length)

    res = Response(data, 206, mimetype=entity.mime_type, direct_passthrough=True)
    res.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(byte1, byte1 + length - 1, size))
    return res


@frappe.whitelist(allow_guest=True)
def list_entity_comments(entity_name):
    Comment = frappe.qb.DocType("Comment")
    User = frappe.qb.DocType("User")
    selectedFields = [
        Comment.comment_by,
        Comment.comment_email,
        Comment.creation,
        Comment.content,
        User.user_image,
    ]

    query = (
        frappe.qb.from_(Comment)
        .inner_join(User)
        .on(Comment.comment_email == User.name)
        .select(*selectedFields)
        .where(
            (Comment.comment_type == "Comment")
            & (Comment.reference_doctype == "Drive File")
            & (Comment.reference_name == entity_name)
        )
        .orderby(Comment.creation, order=Order.asc)
    )
    return query.run(as_dict=True)


@frappe.whitelist()
def set_favourite(entities=None, clear_all=False):
    """
    Favouite or unfavourite DriveEntities for specified user

    :param entities: List[dict] of document names and whether favorite
    :type entity_names: list[str]
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
def remove_or_restore(entity_names, client=None):
    """
    To move entities to or restore entities from the trash

    :param entity_names: List of document-names
    :type entity_names: list[str]
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    manager = FileManager()

    def depth_zero_toggle_is_active(doc):
        if doc.is_active:
            flag = 0
            manager.move_to_trash(doc)
        else:
            storage_data = storage_bar_data(doc.team)
            if (storage_data["limit"] - storage_data["total_size"]) < doc.file_size:
                frappe.throw("You're out of storage!", ValueError)
            manager.restore(doc)
            flag = 1

        doc.is_active = flag
        doc._modified = frappe.utils.now_datetime()
        update_clients(doc.name, doc.team, "upload" if flag else "delete", client)
        folder_size = frappe.db.get_value("Drive File", doc.parent_entity, "file_size")
        frappe.db.set_value(
            "Drive File",
            doc.parent_entity,
            "file_size",
            folder_size + doc.file_size * (1 if flag else -1),
        )

        doc.save()

    for entity in entity_names:
        doc = frappe.get_doc("Drive File", entity)
        if not user_has_permission(doc, "write"):
            raise frappe.PermissionError("You do not have permission to remove this file")
        depth_zero_toggle_is_active(doc)


@frappe.whitelist()
def delete_entities(entity_names=None, clear_all=None):
    if clear_all:
        entity_names = frappe.db.get_list("Drive File", {"is_active": 0, "owner": frappe.session.user}, pluck="name")
    elif isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    elif not isinstance(entity_names, list) or not entity_names:
        frappe.throw(f"Expected non-empty list but got {type(entity_names)}", ValueError)

    for entity in entity_names:
        frappe.get_doc("Drive File", entity).permanent_delete()


@frappe.whitelist(allow_guest=True)
def call_controller_method():
    """
    Call a whitelisted Drive File controller method

    :param entity_name: Document-name of the document on which the controller method is to be called
    :param method: The controller method to be called
    :raises ValueError: If the entity does not exist
    :return: The result of the controller method
    """
    method = frappe.local.form_dict.pop("method")
    entity_name = frappe.local.form_dict.pop("entity_name")
    frappe.local.form_dict.pop("cmd")
    drive_file = frappe.get_doc("Drive File", entity_name)
    if not drive_file:
        frappe.throw("Entity does not exist", ValueError)
    return drive_file.run_method(method, **frappe.local.form_dict)


@frappe.whitelist()
def remove_recents(entity_names=[], clear_all=False):
    """
    Clear recent DriveEntities for specified user

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """
    if clear_all:
        return frappe.db.delete("Drive Entity Log", {"user": frappe.session.user})

    if not isinstance(entity_names, list):
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
def does_entity_exist(name=None, parent_entity=None, team=None):
    if not parent_entity:
        home_folder = get_home_folder(team)
        parent_entity = home_folder.name
    result = frappe.db.exists("Drive File", {"parent_entity": parent_entity, "title": name})
    return result


def auto_delete_from_trash():
    days_before = (date.today() - timedelta(days=30)).isoformat()
    result = frappe.db.get_all(
        "Drive File",
        filters={"is_active": 0, "last_modified": ["<", days_before]},
        fields=["name"],
    )
    delete_entities(result)


def clear_deleted_files():
    days_before = (date.today() + timedelta(days=30)).isoformat()
    result = frappe.db.get_all(
        "Drive File",
        filters={"is_active": -1, "modified": ["<", days_before]},
        fields=["name"],
    )
    for entity in result:
        doc = frappe.get_doc("Drive File", entity, ignore_permissions=True)
        doc.delete()


@frappe.whitelist()
@default_team
def move(entity_names, new_parent=None, team=None, client=None):
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
        doc = frappe.get_doc("Drive File", entity)
        res = doc.move(new_parent, team, client=client)

    if not res["parent_entity"]:
        title, personal = frappe.db.get_value("Drive Team", res["team"], ["title", "personal"])
        res["title"] = "Home" if personal else title

    return res


@frappe.whitelist()
def search(query):
    """
    Basic search implementation
    """
    text = frappe.db.escape(" ".join(k + "*" for k in query.split()))
    teams = get_teams()
    try:
        result = frappe.db.sql(
            f"""
        SELECT  `tabDrive File`.name,
                `tabDrive File`.title,
                `tabDrive File`.is_group,
                `tabDrive File`.is_link,
                `tabDrive File`.mime_type,
                `tabDrive File`.document,
                `tabDrive File`.color,
                `tabUser`.name AS user_name,
                `tabUser`.user_image,
                `tabUser`.full_name
        FROM `tabDrive File`
        LEFT JOIN `tabUser` ON `tabDrive File`.`owner` = `tabUser`.`name`
        WHERE `tabDrive File`.team IN {tuple(teams)}
            AND `tabDrive File`.`is_active` = 1
            AND `tabDrive File`.`parent_entity` <> ''
            AND MATCH(title) AGAINST ({text} IN BOOLEAN MODE)
        GROUP  BY `tabDrive File`.`name`
        """,
            as_dict=1,
        )
        for r in result:
            r["file_type"] = get_file_type(r)
        return result
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Frappe Drive Search Error")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_translate():
    return {
        l["old_name"]: l["name"] for l in frappe.get_all("Drive File", fields=["old_name", "name"]) if l["old_name"]
    }


@frappe.whitelist()
def get_new_title(title, parent_name, folder=False, entity=None):
    """
    Returns new title for an entity if same title exists for another entity at the same level

    :param entity_title: Title of entity to be renamed (if at all)
    :param parent_entity: Parent entity of entity to be renamed (if at all)
    :return: String with new title
    """
    entity_title, entity_ext = os.path.splitext(title)

    filters = {
        "is_active": 1,
        "parent_entity": parent_name,
        "title": ["like", f"{entity_title}%{entity_ext}"],
    }

    if folder:
        filters["is_group"] = 1

    sibling_entity_titles = frappe.db.get_list(
        "Drive File",
        filters=filters,
        fields=["title", "name"],
    )
    if (
        not sibling_entity_titles
        or (sibling_entity_titles[0].name == entity)
        or not any(k["title"] == title for k in sibling_entity_titles)
    ):
        return title
    return f"{entity_title} ({len(sibling_entity_titles)}){entity_ext}"


@frappe.whitelist(allow_guest=True)
def get_entity_type(entity_name):
    entity = frappe.db.get_value(
        "Drive File",
        {"is_active": 1, "name": entity_name},
        ["team", "name", "mime_type", "is_group", "doc"],
        as_dict=1,
    )
    if entity.doc or entity.mime_type == "text/markdown":
        entity["type"] = "document"
    elif entity.is_group:
        entity["type"] = "folder"
    else:
        entity["type"] = "file"
    return entity


@frappe.whitelist()
def get_root_folder(team):
    if team not in get_teams():
        frappe.throw("You can't check the home folder of a team you don't belong to.", frappe.PermissionError)
    return get_home_folder(team)


def auto_delete_transfers():
    from frappe.utils import now_datetime, add_to_date

    one_hour_ago = add_to_date(now_datetime(), hours=-1)

    transfers = frappe.get_all("Drive Transfer", filters={"creation": ["<", one_hour_ago]}, pluck="name")

    for name in transfers:
        frappe.delete_doc("Drive Transfer", name)
