import os, re, json, mimetypes

import frappe
from pypika import Order, functions
from pathlib import Path
from werkzeug.wrappers import Response
from werkzeug.utils import secure_filename, send_file

from drive.utils.files import (
    get_home_folder,
    get_user_directory,
    get_new_title,
    create_thumbnail,
)
from drive.locks.distributed_lock import DistributedLock
from datetime import date, timedelta
import magic
from datetime import datetime
from drive.api.notifications import notify_mentions
from drive.api.storage import storage_bar_data


def if_folder_exists(team, folder_name, parent):
    values = {
        "title": folder_name,
        "is_group": 1,
        "is_active": 1,
        "owner": frappe.session.user,
        "parent_entity": parent,
    }
    existing_folder = frappe.db.get_value(
        "Drive File", values, ["name", "title", "is_group", "is_active"], as_dict=1
    )
    if existing_folder:
        return existing_folder.name
    new_folder = create_folder(team, folder_name, parent)
    return new_folder.name


@frappe.whitelist()
def create_document_entity(title, personal, team, content, parent=None):
    home_directory = get_home_folder(team)
    parent = parent or home_directory.name
    new_title = get_new_title(title, parent)

    if not frappe.has_permission(
        doctype="Drive File",
        doc=parent,
        ptype="write",
        user=frappe.session.user,
    ):
        frappe.throw(
            "Cannot access folder due to insufficient permissions",
            frappe.PermissionError,
        )
    drive_doc = frappe.new_doc("Drive Document")
    drive_doc.title = new_title
    drive_doc.content = content
    drive_doc.version = 2
    drive_doc.save()

    entity = create_drive_file(
        team,
        personal,
        new_title,
        parent,
        0,
        "frappe_doc",
        None,
        lambda _: "",
        document=drive_doc.name,
    )
    return entity


def get_uploads_directory(team_name):
    uploads_path = Path(frappe.get_site_path("private/files"), team_name, "uploads")
    if not os.path.exists(uploads_path):
        uploads_path = Path(frappe.get_site_path("private/files"), team_name, "uploads")
        uploads_path.mkdir()
    return uploads_path


@frappe.whitelist()
def upload_file(team, personal, fullpath=None, parent=None, last_modified=None):
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
    if fullpath:
        dirname = os.path.dirname(fullpath).split("/")
        for i in dirname:
            parent = if_folder_exists(team, i, parent)
    if not frappe.has_permission(
        doctype="Drive File", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Cannot upload due to insufficient permissions", frappe.PermissionError)

    file = frappe.request.files["file"]
    upload_session = frappe.form_dict.uuid
    title = get_new_title(file.filename, parent)

    current_chunk = int(frappe.form_dict.chunk_index)
    total_chunks = int(frappe.form_dict.total_chunk_count)

    site_folder = frappe.get_site_path("private/files")
    temp_path = (
        get_uploads_directory(home_folder["name"]) / f"{upload_session}_{secure_filename(title)}"
    )

    storage_data = storage_bar_data(team)
    if (storage_data["limit"] - storage_data["total_size"]) < int(
        frappe.form_dict.total_file_size
    ):
        frappe.throw("You're out of storage!", ValueError)

    with temp_path.open("ab") as f:
        f.seek(int(frappe.form_dict.chunk_byte_offset))
        f.write(file.stream.read())
        if not f.tell() >= int(frappe.form_dict.total_file_size):
            return
        else:
            pass

    if current_chunk == total_chunks - 1:
        file_size = temp_path.stat().st_size
        if file_size != int(frappe.form_dict.total_file_size):
            temp_path.unlink()
            frappe.throw("Size on disk does not match specified filesize.", ValueError)

        mime_type, _ = mimetypes.guess_type(temp_path)

        if mime_type is None:
            # Read the first 2KB of the binary stream to determine the file type if string checking failed
            # Do a rejection workflow to reject undesired mime types
            mime_type = magic.from_buffer(open(temp_path, "rb").read(2048), mime=True)
        drive_file = create_drive_file(
            team,
            personal,
            title,
            parent,
            file_size,
            mime_type,
            last_modified,
            lambda n: Path(home_folder["name"]) / f"{n}{temp_path.suffix}",
        )
        os.rename(temp_path, Path(site_folder) / drive_file.path)

        if mime_type.startswith(("image", "video")):
            frappe.enqueue(
                create_thumbnail,
                queue="default",
                timeout=None,
                now=True,
                at_front=True,
                # will set to false once reactivity in new UI is solved
                entity_name=drive_file.name,
                path=Path(frappe.get_site_path("private/files")) / drive_file.path,
                mime_type=mime_type,
                team=team,
            )
        return drive_file


def create_drive_file(
    team, personal, title, parent, file_size, mime_type, last_modified, entity_path, document=None
):
    drive_file = frappe.get_doc(
        {
            "doctype": "Drive File",
            "team": team,
            "is_private": personal,
            "title": title,
            "parent_entity": parent,
            "file_size": file_size,
            "mime_type": mime_type,
            "document": document,
        }
    )
    drive_file.flags.file_created = True
    drive_file.insert()
    drive_file.path = str(entity_path(drive_file.name))
    drive_file.save()
    if last_modified:
        dt_object = datetime.fromtimestamp(int(last_modified) / 1000.0)
        formatted_datetime = dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")
        drive_file.db_set("modified", formatted_datetime, update_modified=False)
    return drive_file


@frappe.whitelist()
def create_folder(team, title, personal=False, parent=None):
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

    if not frappe.has_permission(
        doctype="Drive File", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw(
            "Cannot create folder due to insufficient permissions",
            frappe.PermissionError,
        )
    if not personal:
        entity_exists = frappe.db.exists(
            {
                "doctype": "Drive File",
                "parent_entity": parent,
                "is_group": 1,
                "title": title,
                "is_active": 1,
                "is_private": 0,
            }
        )
    else:
        entity_exists = frappe.db.exists(
            {
                "doctype": "Drive File",
                "parent_entity": parent,
                "title": title,
                "is_group": 1,
                "is_active": 1,
                "owner": frappe.session.user,
                "is_private": 1,
            }
        )
    print(title, entity_exists)
    if entity_exists:
        suggested_name = get_new_title(title, parent, folder=True)
        frappe.throw(
            f"Folder '{title}' already exists.\n Suggested: {suggested_name}",
            FileExistsError,
        )

    drive_file = frappe.get_doc(
        {
            "doctype": "Drive File",
            "title": title,
            "team": team,
            "is_group": 1,
            "parent_entity": parent,
            "color": "#525252",
            "is_private": personal,
        }
    )
    drive_file.insert()

    return drive_file


@frappe.whitelist()
def create_link(team, title, link, personal=False, parent=None):
    home_folder = get_home_folder(team)
    parent = parent or home_folder.name

    if not frappe.has_permission(
        doctype="Drive File", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw(
            "Cannot create folder due to insufficient permissions",
            frappe.PermissionError,
        )
    if not personal:
        entity_exists = frappe.db.exists(
            {
                "doctype": "Drive File",
                "parent_entity": parent,
                "title": title,
                "is_active": 1,
                "is_link": 1,
            }
        )
    else:
        entity_exists = frappe.db.exists(
            {
                "doctype": "Drive File",
                "parent_entity": parent,
                "title": title,
                "is_link": 1,
                "is_active": 1,
                "owner": frappe.session.user,
                "is_private": 1,
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
            "parent_entity": parent,
            "is_private": personal,
        }
    )
    drive_file.insert()

    return drive_file


@frappe.whitelist()
def save_doc(entity_name, doc_name, raw_content, content, file_size, mentions, settings=None):
    if not frappe.has_permission(
        doctype="Drive File",
        doc=entity_name,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to view this file")
    if settings:
        frappe.db.set_value("Drive Document", doc_name, "settings", json.dumps(settings))
    file_size = len(content.encode("utf-8")) + len(raw_content.encode("utf-8"))
    frappe.db.set_value("Drive Document", doc_name, "content", content)
    frappe.db.set_value("Drive Document", doc_name, "raw_content", raw_content)
    frappe.db.set_value("Drive Document", doc_name, "mentions", json.dumps(mentions))
    frappe.db.set_value("Drive File", entity_name, "file_size", file_size)
    if json.dumps(mentions):
        frappe.enqueue(
            notify_mentions,
            queue="long",
            job_id=f"fdoc_{doc_name}",
            deduplicate=True,
            timeout=None,
            now=False,
            at_front=False,
            entity_name=entity_name,
            document_name=doc_name,
        )
    return


@frappe.whitelist()
def create_doc_version(entity_name, doc_name, snapshot_data, snapshot_message):
    if not frappe.has_permission(
        doctype="Drive File",
        doc=entity_name,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.permissionerror("you do not have permission to view this file")
    new_version = frappe.new_doc("drive document version")
    new_version.snapshot_data = snapshot_data
    new_version.parent_entity = entity_name
    new_version.snapshot_message = snapshot_message
    new_version.parent_document = doc_name
    new_version.snapshot_size = len(snapshot_data.encode("utf-8"))
    new_version.save()
    return


@frappe.whitelist()
def get_doc_version_list(entity_name):
    if not frappe.has_permission(
        doctype="Drive File",
        doc=entity_name,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to view this file")
    return frappe.get_list(
        "Drive Document Version",
        filters={"parent_entity": entity_name},
        order_by="creation desc",
        fields=["*"],
    )


@frappe.whitelist(allow_guest=True)
def get_file_content(entity_name, trigger_download=0):  #
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param trigger_download: 1 to trigger the "Save As" dialog. Defaults to 0
    :type trigger_download: int
    :raises ValueError: If the DriveEntity doc does not exist or is not a file
    :raises PermissionError: If the current user does not have permission to read the file
    :raises FileLockedError: If the file has been writer-locked
    """

    if not frappe.has_permission(
        doctype="Drive File",
        doc=entity_name,
        ptype="read",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to view this file")
    trigger_download = int(trigger_download)
    drive_file = frappe.get_value(
        "Drive File",
        {"name": entity_name, "is_active": 1},
        [
            "is_group",
            "path",
            "title",
            "mime_type",
            "file_size",
            "is_active",
            "owner",
        ],
        as_dict=1,
    )
    if not drive_file or drive_file.is_group or drive_file.is_active != 1:
        frappe.throw("Not found", frappe.NotFound)

    path = Path(frappe.get_site_path("private/files")) / drive_file.path
    with DistributedLock(path, exclusive=False):
        return send_file(
            path,
            mimetype=drive_file.mime_type,
            as_attachment=trigger_download,
            conditional=True,
            max_age=3600,
            download_name=drive_file.title,
            environ=frappe.request.environ,
        )


def stream_file_content(drive_file, range_header):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param drive_file: Drive File record object
    """
    path = Path(frappe.get_site_path("private/files")) / drive_file.path
    size = os.path.getsize(path)
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

    data = None
    with open(path, "rb") as f:
        f.seek(byte1)
        data = f.read(length)

    res = Response(data, 206, mimetype=mimetypes.guess_type(path)[0], direct_passthrough=True)
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
def unshare_entities(entity_names, move=False):
    """
    Unshare DriveEntities

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :param move: if True, moves entity to root entity of user
    :type move: Boolean
    :raises ValueError: If decoded entity_names is not a list
    """

    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    for entity in entity_names:
        doc = frappe.get_doc("Drive File", entity)
        if not doc:
            frappe.throw("Entity does not exist", ValueError)
        if move:
            doc.move()
        doc.unshare(frappe.session.user)


def delete_background_job(entity, ignore_permissions):
    frappe.delete_doc("Drive File", entity, ignore_permissions=ignore_permissions)


@frappe.whitelist()
def delete_entities(entity_names=None, clear_all=None):
    """
    Delete DriveEntities

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """
    if clear_all:
        entity_names = frappe.db.get_list(
            "Drive File", {"is_active": 0, "owner": frappe.session.user}, pluck="name"
        )
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    for entity in entity_names:
        root_entity = get_ancestors_of(entity)
        if root_entity:
            root_entity = get_ancestors_of(entity)[0]
        else:
            root_entity = get_user_directory()
        owns_root_entity = frappe.has_permission(
            doctype="Drive File",
            doc=root_entity,
            ptype="write",
            user=frappe.session.user,
        )
        has_write_access = frappe.has_permission(
            doctype="Drive File", doc=entity, ptype="write", user=frappe.session.user
        )
        ignore_permissions = owns_root_entity or has_write_access
        frappe.db.set_value("Drive File", entity, "is_active", -1)
        frappe.enqueue(
            delete_background_job,
            queue="default",
            timeout=None,
            entity=entity,
            ignore_permissions=ignore_permissions,
        )


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
        print(entity)
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


# def toggle_is_active(doc):
#     doc.is_active = 0 if doc.is_active else 1
#     frappe.db.set_value('Drive File', doc.name, 'is_active',doc.is_active)
#     for child in doc.get_children():
#         toggle_is_active(child)


@frappe.whitelist()
def remove_or_restore(entity_names, team):
    """
    To move entities to or restore entities from the trash

    :param entity_names: List of document-names
    :type entity_names: list[str]
    """
    storage_data = storage_bar_data(team)

    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)

    def depth_zero_toggle_is_active(doc):
        if doc.is_active:
            doc.is_active = 0
        else:
            if (storage_data["limit"] - storage_data["total_size"]) < doc.file_size:
                frappe.throw("You're out of storage!", ValueError)
            doc.is_active = 1
        doc.save()

    for entity in entity_names:
        doc = frappe.get_doc("Drive File", entity)
        if not frappe.has_permission(
            doctype="Drive File", user=frappe.session.user, doc=doc, ptype="write"
        ):
            raise frappe.PermissionError("You do not have permission to remove this file")
        depth_zero_toggle_is_active(doc)


@frappe.whitelist(allow_guest=True)
def call_controller_method(entity_name, method):
    """
    Call a whitelisted Drive File controller method

    :param entity_name: Document-name of the document on which the controller method is to be called
    :param method: The controller method to be called
    :raises ValueError: If the entity does not exist
    :return: The result of the controller method
    """
    # broken
    drive_file = frappe.get_doc("Drive File", frappe.local.form_dict.pop("entity_name"))
    if not drive_file:
        frappe.throw("Entity does not exist", ValueError)
    method = frappe.local.form_dict.pop("method")
    drive_file.is_whitelisted(method)
    frappe.local.form_dict.pop("cmd")
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
def get_children_count(drive_file):
    children_count = frappe.db.count("Drive File", {"parent_entity": drive_file, "is_active": 1})
    return children_count


@frappe.whitelist()
def does_entity_exist(name=None, parent_entity=None):
    result = frappe.db.exists("Drive File", {"parent_entity": parent_entity, "title": name})
    return bool(result)


def auto_delete_from_trash():
    days_before = (date.today() - timedelta(days=30)).isoformat()
    result = frappe.db.get_all(
        "Drive File",
        filters={"is_active": 0, "trashed_on": ["<", days_before]},
        fields=["name"],
    )
    delete_entities(result)


@frappe.whitelist()
def get_title(entity_name):
    """
    Toggle allow download for entity

    """
    if not frappe.has_permission(
        doctype="Drive File", doc=entity_name, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Not permitted", frappe.PermissionError)
    return frappe.db.get_value("Drive File", entity_name, "title")


@frappe.whitelist()
def move(entity_names, new_parent=None):
    """
    Move file or folder to the new parent folder

    :param new_parent: Document-name of the new parent folder. Defaults to the user directory
    :raises NotADirectoryError: If the new_parent is not a folder, or does not exist
    :raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
    :return: DriveEntity doc once file is moved
    """

    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    for entity in entity_names:
        doc = frappe.get_doc("Drive File", entity)
        doc.move(new_parent)
        doc.save()

    return


@frappe.whitelist()
def search(query, home_dir):
    """
    Placeholder search implementation
    """
    text = frappe.db.escape(query + "*")
    user = frappe.db.escape(frappe.session.user)
    omit = frappe.db.escape(home_dir)
    try:
        result = frappe.db.sql(
            f"""
        SELECT  `tabDrive File`.name,
                `tabDrive File`.title, 
                `tabDrive File`.owner,
                `tabDrive File`.mime_type,
                `tabDrive File`.is_group,
                `tabDrive File`.document,
                `tabDrive File`.color,
                `tabUser`.user_image,
                `tabUser`.full_name
        FROM `tabDrive File`
        LEFT JOIN `tabDrive DocShare`
        ON `tabDrive DocShare`.`share_name` = `tabDrive File`.`name`
        LEFT JOIN `tabUser Group Member`
        ON `tabUser Group Member`.`parent` = `tabDrive DocShare`.`user_name`
        LEFT JOIN `tabUser` ON `tabDrive File`.`owner` = `tabUser`.`email`
        WHERE (`tabUser Group Member`.`user` = {user} 
                OR `tabDrive DocShare`.`user_name` = {user} 
                OR `tabDrive DocShare`.`everyone` = 1 
                OR `tabDrive File`.`owner` = {user})
            AND `tabDrive File`.`is_active` = 1
            AND MATCH(title) AGAINST ({text} IN BOOLEAN MODE)
            AND NOT `tabDrive File`.`name` LIKE {omit}
        GROUP  BY `tabDrive File`.`name` 
        """,
            as_dict=1,
        )
        return result
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Frappe Drive Search Error")
        return {"error": str(e)}


@frappe.whitelist()
def get_ancestors_of(entity_name):
    """
    Return all parent nodes till the root node
    """
    # CONCAT_WS('/', t.title, gp.path),
    entity_name = frappe.db.escape(entity_name)
    result = frappe.db.sql(
        f"""
        WITH RECURSIVE generated_path as ( 
        SELECT 
            `tabDrive File`.name,
            `tabDrive File`.parent_entity
        FROM `tabDrive File` 
        WHERE `tabDrive File`.name = {entity_name}

        UNION ALL

        SELECT 
            t.name,
            t.parent_entity
        FROM generated_path as gp
        JOIN `tabDrive File` as t ON t.name = gp.parent_entity) 
        SELECT name FROM generated_path;
    """,
        as_dict=0,
    )
    # Match the output of frappe/nested.py get_ancestors_of
    flattened_list = [item for sublist in result for item in sublist]
    flattened_list.pop(0)
    return flattened_list


@frappe.whitelist(allow_guest=True)
def upload_chunked_file(personal=0, parent=None, last_modified=None):
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

    parent = frappe.form_dict.parent
    drive_entity = frappe.get_value(
        "Drive File",
        parent,
        ["document", "title", "mime_type", "file_size", "owner", "team"],
        as_dict=1,
    )
    home_directory = get_home_folder(drive_entity.team)
    embed_directory = Path(
        frappe.get_site_path("private/files"),
        home_directory.name,
        "embeds",
    )
    if not frappe.has_permission(
        doctype="Drive File", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Cannot upload due to insufficient permissions", frappe.PermissionError)

    file = frappe.request.files["file"]

    name = frappe.form_dict.uuid
    title, file_ext = os.path.splitext(frappe.form_dict.file_name)
    mime_type = frappe.form_dict.mime_type
    current_chunk = int(frappe.form_dict.chunk_index)
    total_chunks = int(frappe.form_dict.total_chunk_count)
    file_size = int(frappe.form_dict.total_file_size)
    save_path = Path(embed_directory) / f"{secure_filename(name+file_ext)}"
    if current_chunk == 0 and save_path.exists():
        frappe.throw(f"File '{title}' already exists", FileExistsError)

    if not mime_type:
        mime_type = magic.from_buffer(open(save_path, "rb").read(2048), mime=True)

    with save_path.open("ab") as f:
        f.seek(int(frappe.form_dict.chunk_byte_offset))
        f.write(file.stream.read())

    if current_chunk + 1 == total_chunks:
        file_size = save_path.stat().st_size

    if file_size != int(frappe.form_dict.total_file_size):
        save_path.unlink()
        frappe.throw("Size on disk does not match specified filesize", ValueError)
    drive_file = create_drive_file(
        drive_entity.team,
        personal,
        title,
        parent,
        file_size,
        mime_type,
        last_modified,
        lambda n: Path(home_directory["name"]) / "embeds" / f"{n}{save_path.suffix}",
    )
    os.rename(save_path, frappe.get_site_path("private/files") / drive_file.path)

    return drive_file.name + save_path.suffix


@frappe.whitelist()
def get_translate():
    return {
        l["old_name"]: l["name"]
        for l in frappe.get_list("Drive File", fields=["old_name", "name"])
        if l["old_name"]
    }
