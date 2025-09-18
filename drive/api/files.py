import json
import os
import re
from datetime import date, datetime, timedelta
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
	if_folder_exists,
	strip_comment_spans,
	update_file_size,
)
from drive.utils.files import FileManager

from .permissions import user_has_permission


@frappe.whitelist()
def upload_embed(doc):
    doc = frappe.get_doc("Drive File", doc)
    file = frappe.request.files["file"]
    file.filename = "Embed - " + doc

    embed = upload_file(doc.team, parent=doc, embed=1)
    return {
        "file_url": f"/api/method/drive.api.embed.get_file_content?embed_name={embed.name}&parent_entity_name={doc}"
    }


@frappe.whitelist(allow_guest=True)
@default_team
def upload_file(
    team=None,
    total_file_size=0,
    last_modified=None,
    fullpath=None,
    parent=None,
    embed=0,
):
    """
    Accept chunked file contents via a multipart upload, store the file on
    disk, and insert a corresponding DriveEntity doc.

    :param fullpath: Full path of the uploaded file
    :param parent: Document-name of the parent folder. Defaults to the user directory
    :raises PermissionError: If the user does not have write access to the specified parent folder
    :raises FileExistsError: If a file with the same name already exists in the specified parent folder
    :raises ValueError: If the size of the stored file does not match the specified filesize
    :return: DriveEntity doc once the entire file has been uploaded
    """
    home_folder = get_home_folder(team)
    parent = parent or home_folder["name"]
    if not user_has_permission(parent, "upload"):
        frappe.throw("Ask the folder owner for upload access.", frappe.PermissionError)
    embed = int(embed)

    if fullpath:
        dirname = os.path.dirname(fullpath).split("/")
        for i in dirname:
            parent = if_folder_exists(team, i, parent)

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
    title = get_new_title(file.filename, parent)
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
    manager.upload_file(temp_path, drive_file)
    update_file_size(parent, file_size)

    return drive_file


@frappe.whitelist()
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
                with manager.get_file(drive_file.path) as f:
                    thumbnail_data = f.read()[:1000].decode("utf-8").replace("\n", "<br/>")
            elif drive_file.mime_type == "frappe_doc":
                html = frappe.get_value("Drive Document", drive_file.document, "raw_content")
                thumbnail_data = html[:1000] if html else ""
            elif drive_file.mime_type == "frappe/slides":
                thumbnail_data = "none"
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
        except FileNotFoundError as e:
            print(e)
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
def create_presentation(title, team, parent=None):
    home_directory = get_home_folder(team)
    parent = parent or home_directory.name
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
def create_document_entity(title, team, parent=None):
    home_directory = get_home_folder(team)
    parent = parent or home_directory.name
    if not user_has_permission(parent, "upload"):
        frappe.throw(
            "Cannot access folder due to insufficient permissions",
            frappe.PermissionError,
        )
    drive_doc = frappe.new_doc("Drive Document")
    drive_doc.title = title
    drive_doc.version = 2
    drive_doc.save()

    entity = create_drive_file(
        team,
        title,
        parent,
        "frappe_doc",
        lambda _: "",
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
                "parent_path": Path(parent_doc.path or ""),
                "parent_entity": parent_doc.name,
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


@frappe.whitelist()
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
            "_modified": datetime.now(),
            "parent_entity": parent,
        }
    )
    drive_file.insert()

    return drive_file


@frappe.whitelist(allow_guest=True)
def save_doc(entity_name, doc_name=None, content=None, yjs=None, comment=False):
    # BROKEN
    # In Collab mode file size is off + mentions don't work.
    can_write = user_has_permission(entity_name, "write")
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
        except frappe.exceptions.QueryDeadlockError:
            if yjs:
                # Pass if there's a deadlock, as CRDT is supposed to take care of it.
                frappe.log_error(
                    f"There was a collision, not storing data -{entity_name}, {doc_name}"
                )
            else:
                frappe.throw("There was a conflict - consider turning on collaborative mode.")
    else:
        # Text based files
        # BROKEN - should reparse markdown files.
        h = html2text.HTML2Text()
        h.body_width = 0
        md_content = h.handle(content)
        path = frappe.db.get_value("Drive File", entity_name, "path")
        FileManager().write_file(path, md_content)

    file = frappe.get_doc("Drive File", entity_name)
    file._modified = datetime.now()
    if content:
        file.file_size = len(content.encode("utf-8"))
    if yjs:
        file.file_size = len(yjs.encode("utf-8"))
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


@frappe.whitelist()
def create_auth_token(entity_name):
    if not user_has_permission(entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")
    settings = frappe.get_single("Drive Disk Settings")
    key = settings.get_password("jwt_key", raise_exception=False)
    return jwt.encode(
        {"name": entity_name, "expiry": (datetime.now() + timedelta(minutes=1)).timestamp()},
        key=key,
    )


@frappe.whitelist(allow_guest=True)
def get_file_content(entity_name, trigger_download=0, jwt_token=None):
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
        if datetime.now().timestamp() > auth["expiry"] or auth["name"] != entity_name:
            raise frappe.PermissionError("You do not have permission to view this file")
    elif not user_has_permission(entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    trigger_download = int(trigger_download)
    drive_file = frappe.get_value(
        "Drive File",
        {"name": entity_name, "is_active": 1},
        [
            "is_group",
            "is_link",
            "path",
            "title",
            "mime_type",
            "file_size",
            "is_active",
            "owner",
            "document",
        ],
        as_dict=1,
    )
    if not drive_file or drive_file.is_group or drive_file.is_link or drive_file.is_active != 1:
        frappe.throw("Not found", frappe.NotFound)

    if drive_file.document:
        html = frappe.get_value("Drive Document", drive_file.document, "raw_content")
        return html
    else:
        manager = FileManager()
        return send_file(
            manager.get_file(drive_file.path),
            mimetype=drive_file.mime_type,
            as_attachment=trigger_download,
            conditional=True,
            max_age=3600,
            download_name=drive_file.title,
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
def remove_or_restore(entity_names):
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
        entity_names = frappe.db.get_list(
            "Drive File", {"is_active": 0, "owner": frappe.session.user}, pluck="name"
        )
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
def does_entity_exist(name=None, parent_entity=None):
    result = frappe.db.exists("Drive File", {"parent_entity": parent_entity, "title": name})
    return bool(result)


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
def move(entity_names, new_parent=None, team=None):
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
        res = doc.move(new_parent, team)

    if not res["parent_entity"]:
        title, personal = frappe.db.get_value("Drive Team", res["team"], ["title", "personal"])
        res["title"] = "Home" if personal else title

    return res


@frappe.whitelist()
def search(query, team):
    """
    Basic search implementation
    """
    text = frappe.db.escape(" ".join(k + "*" for k in query.split()))
    user = frappe.db.escape(frappe.session.user)
    team = frappe.db.escape(team)
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
        WHERE `tabDrive File`.team = {team}
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


@frappe.whitelist()
def get_translate():
    return {
        l["old_name"]: l["name"]
        for l in frappe.get_list("Drive File", fields=["old_name", "name"])
        if l["old_name"]
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
        pluck="title",
    )
    if not sibling_entity_titles or (
        len(sibling_entity_titles) == 1 and sibling_entity_titles[0] == entity
    ):
        return title
    return f"{entity_title} ({len(sibling_entity_titles)}){entity_ext}"


@frappe.whitelist(allow_guest=True)
def get_entity_type(entity_name):
    entity = frappe.db.get_value(
        "Drive File",
        {"is_active": 1, "name": entity_name},
        ["team", "name", "mime_type", "is_group", "document"],
        as_dict=1,
    )
    if entity.document or entity.mime_type == "text/markdown":
        entity["type"] = "document"
    elif entity.is_group:
        entity["type"] = "folder"
    else:
        entity["type"] = "file"
    return entity
