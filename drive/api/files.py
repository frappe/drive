import frappe
import os
import re
from frappe.utils.nestedset import rebuild_tree, get_ancestors_of
from pypika import Order, Field, functions as fn
from pathlib import Path
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from werkzeug.utils import secure_filename
import uuid
import mimetypes
import hashlib
import json
from drive.utils.files import (
    get_user_directory,
    create_user_directory,
    get_new_title,
    get_user_thumbnails_directory,
    create_user_thumbnails_directory,
    create_thumbnail,
)
from drive.locks.distributed_lock import DistributedLock
from datetime import date, timedelta
import magic
from datetime import datetime
import urllib.parse


def if_folder_exists(folder_name, parent):
    values = {
        "title": folder_name,
        "is_group": 1,
        "is_active": 1,
        "owner": frappe.session.user,
        "parent_drive_entity": parent,
    }
    existing_folder = frappe.db.get_value(
        "Drive Entity", values, ["name", "title", "is_group", "is_active"], as_dict=1
    )
    if existing_folder:
        return existing_folder.name
    new_folder = create_folder(folder_name, parent)
    return new_folder.name


@frappe.whitelist()
def get_home_folder_id(user=None):
    """Returns user directory name from user's unique id"""
    if not user:
        user = frappe.session.user
        return get_user_directory(user).name


@frappe.whitelist()
def create_document_entity(title, content, parent=None):
    try:
        user_directory = get_user_directory()
    except FileNotFoundError:
        user_directory = create_user_directory()
    new_title = get_new_title(title, parent)

    parent = frappe.form_dict.parent or user_directory.name

    if not frappe.has_permission(
        doctype="Drive Entity",
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
    drive_doc.save()

    drive_entity = frappe.new_doc("Drive Entity")
    drive_entity.title = new_title
    drive_entity.name = uuid.uuid4().hex
    drive_entity.parent_drive_entity = parent
    drive_entity.mime_type = "frappe_doc"
    drive_entity.document = drive_doc

    drive_entity.flags.file_created = True
    drive_entity.save()
    return drive_entity


@frappe.whitelist()
def upload_file(fullpath=None, parent=None, last_modified=None):
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
    try:
        user_directory = get_user_directory()
    except FileNotFoundError:
        user_directory = create_user_directory()

    parent = frappe.form_dict.parent or user_directory.name

    if fullpath:
        dirname = os.path.dirname(fullpath).split("/")
        for i in dirname:
            parent = if_folder_exists(i, parent)

    if not frappe.has_permission(
        doctype="Drive Entity", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Cannot upload due to insufficient permissions", frappe.PermissionError)

    file = frappe.request.files["file"]
    title = get_new_title(file.filename, parent)

    current_chunk = int(frappe.form_dict.chunk_index)
    total_chunks = int(frappe.form_dict.total_chunk_count)

    save_path = Path(user_directory.path) / f"{parent}_{secure_filename(title)}"

    if current_chunk == 0 and save_path.exists():
        frappe.throw(f"File '{title}' already exists", FileExistsError)

    with save_path.open("ab") as f:
        f.seek(int(frappe.form_dict.chunk_byte_offset))
        f.write(file.stream.read())

    if current_chunk + 1 == total_chunks:
        file_size = save_path.stat().st_size
        if file_size != int(frappe.form_dict.total_file_size):
            save_path.unlink()
            frappe.throw("Size on disk does not match specified filesize", ValueError)

        mime_type, _ = mimetypes.guess_type(save_path)

        if mime_type is None:
            # Read the first 2KB of the binary stream to determine the file type if string checking failed
            # Do a rejection workflow to reject undesired mime types
            mime_type = magic.from_buffer(open(save_path, "rb").read(2048), mime=True)

        file_name, file_ext = os.path.splitext(title)
        name = uuid.uuid4().hex
        path = save_path.parent / f"{name}{save_path.suffix}"
        save_path.rename(path)

        drive_entity = create_drive_entity(
            name, title, parent, path, file_size, file_ext, mime_type, last_modified
        )

        if mime_type.startswith(("image", "video")):
            frappe.enqueue(
                create_thumbnail,
                queue="default",
                timeout=None,
                now=True,
                at_front=True,
                # will set to false once reactivity in new UI is solved
                entity_name=name,
                path=path,
                mime_type=mime_type,
            )
        return drive_entity


def create_drive_entity(name, title, parent, path, file_size, file_ext, mime_type, last_modified):
    drive_entity = frappe.get_doc(
        {
            "doctype": "Drive Entity",
            "name": name,
            "title": title,
            "parent_drive_entity": parent,
            "path": path,
            "file_size": file_size,
            "file_ext": file_ext,
            "mime_type": mime_type,
        }
    )
    drive_entity.flags.file_created = True
    drive_entity.insert()
    if last_modified:
        dt_object = datetime.fromtimestamp(int(last_modified) / 1000.0)
        formatted_datetime = dt_object.strftime("%Y-%m-%d %H:%M:%S.%f")
        drive_entity.db_set("modified", formatted_datetime, update_modified=False)
    return drive_entity


@frappe.whitelist()
def create_folder(title, parent=None):
    """
    Create a new folder.

    :param title: Folder name
    :param parent: Document-name of the parent folder. Defaults to the user directory
    :raises PermissionError: If the user does not have write access to the specified parent folder
    :raises FileExistsError: If a folder with the same name already exists in the specified parent folder
    :return: DriveEntity doc of the new folder
    """

    try:
        user_directory = get_user_directory()
    except FileNotFoundError:
        user_directory = create_user_directory()

    parent = parent or user_directory.name
    if not frappe.has_permission(
        doctype="Drive Entity", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw(
            "Cannot create folder due to insufficient permissions",
            frappe.PermissionError,
        )

    entity_exists = frappe.db.exists(
        {"doctype": "Drive Entity", "parent_drive_entity": parent, "title": title}
    )
    if entity_exists:
        suggested_name = get_new_title(title, parent)
        frappe.throw(
            f"Folder '{title}' already exists.\n Suggested: {suggested_name}",
            FileExistsError,
        )

    drive_entity = frappe.get_doc(
        {
            "doctype": "Drive Entity",
            "name": uuid.uuid4().hex,
            "title": title,
            "is_group": 1,
            "parent_drive_entity": parent,
            "color": "#525252",
        }
    )
    drive_entity.insert()

    return drive_entity


def get_doc_content(drive_document_name):
    drive_document = frappe.db.get_value(
        "Drive Document",
        drive_document_name,
        ["content"],
        as_dict=1,
    )
    return drive_document


""" @frappe.whitelist()
def rename_doc_entity(entity_name, title):
    doc_name = frappe.db.get_value("Drive Entity", entity_name, "document")
    frappe.db.set_value("Drive Document", doc_name, "title", title)
    frappe.db.set_value("Drive Entity", entity_name, "title", title)
    return """


@frappe.whitelist()
def save_doc(entity_name, doc_name, content, file_size):
    if not frappe.has_permission(
        doctype="Drive Entity",
        doc=entity_name,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to view this file")
    drive_document = frappe.db.set_value("Drive Document", doc_name, "content", content)
    frappe.db.set_value("Drive Entity", entity_name, "file_size", file_size)
    return


@frappe.whitelist(allow_guest=True)
def get_file_content(entity_name, trigger_download=0):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param trigger_download: 1 to trigger the "Save As" dialog. Defaults to 0
    :type trigger_download: int
    :raises ValueError: If the DriveEntity doc does not exist or is not a file
    :raises PermissionError: If the current user does not have permission to read the file
    :raises FileLockedError: If the file has been writer-locked
    """

    is_public = False
    if frappe.db.exists(
        {
            "doctype": "Drive DocShare",
            "share_doctype": "Drive Entity",
            "share_name": entity_name,
            "public": 1,
        }
    ):
        is_public = True
    if not is_public:
        if not frappe.has_permission(
            doctype="Drive Entity",
            doc=entity_name,
            ptype="read",
            user=frappe.session.user,
        ):
            raise frappe.PermissionError("You do not have permission to view this file")
    trigger_download = int(trigger_download)
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["is_group", "path", "title", "mime_type", "file_size"],
        as_dict=1,
    )
    if not drive_entity or drive_entity.is_group:
        raise ValueError

    with DistributedLock(drive_entity.path, exclusive=False):
        try:
            file = open(drive_entity.path, "rb")
        except TypeError:
            response = Response(frappe.request.environ)
            response.status_code = 204
            return response

        response = Response(wrap_file(frappe.request.environ, file), direct_passthrough=True)
        response.mimetype = drive_entity.mime_type or "application/octet-stream"
        content_dispostion = "attachment" if trigger_download else "inline"
        response.headers.add(
            "Content-Disposition",
            content_dispostion,
            filename=format(urllib.parse.quote(drive_entity.title.encode("utf8"))),
        )
        response.headers.add("Content-Length", str(drive_entity.file_size))
        response.headers.add("Content-Type", response.mimetype)
        response.headers.add("Accept-Range", "bytes")

        range_header = frappe.request.headers.get("Range", None)
        if range_header:
            return stream_file_content(drive_entity, range_header)

        return response


def stream_file_content(drive_entity, range_header):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param drive_entity: Drive Entity record object
    """

    # range_header = frappe.request.headers.get("Range", None)
    size = os.path.getsize(drive_entity.path)
    byte1, byte2 = 0, None

    m = re.search("(\d+)-(\d*)", range_header)
    g = m.groups()

    if g[0]:
        byte1 = int(g[0])
    if g[1]:
        byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1

    data = None
    with open(drive_entity.path, "rb") as f:
        f.seek(byte1)
        data = f.read(length)

    res = Response(
        data, 206, mimetype=mimetypes.guess_type(drive_entity.path)[0], direct_passthrough=True
    )
    res.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(byte1, byte1 + length - 1, size))
    return res


@frappe.whitelist(allow_guest=True)
def list_folder_contents(entity_name=None, order_by="modified", is_active=1):
    """
    Return list of DriveEntity records present in this folder

    :param entity_name: Document-name of the folder whose contents are to be listed. Defaults to the user directory
    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :raises PermissionError: If the user does not have access to the specified folder
    :return: List of DriveEntity records
    :rtype: list
    """

    try:
        entity_name = entity_name or get_user_directory().name
    except FileNotFoundError:
        return []
    parent_is_group, parent_is_active = frappe.db.get_value(
        "Drive Entity", entity_name, ["is_group", "is_active"]
    )
    if not parent_is_group:
        frappe.throw("Specified entity is not a folder", NotADirectoryError)
    if not parent_is_active:
        frappe.throw("Specified folder has been trashed by the owner")
    is_public = False
    if frappe.db.exists(
        {
            "doctype": "Drive DocShare",
            "share_doctype": "Drive Entity",
            "share_name": entity_name,
            "public": 1,
        }
    ):
        is_public = True
    if not is_public:
        if not frappe.has_permission(
            doctype="Drive Entity",
            doc=entity_name,
            ptype="read",
            user=frappe.session.user,
        ):
            frappe.throw(
                "Cannot access folder due to insufficient permissions",
                frappe.PermissionError,
            )
    general_access_val = "public" if is_public else "everyone"
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    DriveUser = frappe.qb.DocType("User")
    UserGroupMember = frappe.qb.DocType("User Group Member")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveEntity.owner,
        DriveUser.full_name,
        DriveUser.user_image,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_download,
        DriveEntity.is_active,
        DriveEntity.allow_comments,
        DriveDocShare.read,
        DriveDocShare.user_name,
        fn.Max(DriveDocShare.write).as_("write"),
        DriveDocShare.public,
        DriveDocShare.everyone,
        DriveDocShare.share,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .inner_join(DriveDocShare)
        .on((DriveDocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on((UserGroupMember.parent == DriveDocShare.user_name))
        .left_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .select(*selectedFields)
        .where(
            (DriveEntity.parent_drive_entity == entity_name)
            & (DriveEntity.is_active == 1)
            & (
                (UserGroupMember.user == frappe.session.user)
                | (
                    (DriveDocShare.user_name == frappe.session.user)
                    | (DriveDocShare[general_access_val] == 1)
                )
            )
        )
        .groupby(DriveEntity.name)
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    result = query.run(as_dict=True)
    return result


@frappe.whitelist()
def list_owned_entities(entity_name=None, order_by="modified", is_active=1):
    """
    Return list of DriveEntity records present in this folder

    :param entity_name: Document-name of the folder whose contents are to be listed. Defaults to the user directory
    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :raises PermissionError: If the user does not have access to the specified folder
    :return: List of DriveEntity records
    :rtype: list
    """

    try:
        entity_name = entity_name or get_user_directory().name
    except FileNotFoundError:
        return []
    parent_is_group, parent_is_active, parent_owner = frappe.db.get_value(
        "Drive Entity", entity_name, ["is_group", "is_active", "owner"]
    )
    if not parent_is_group:
        frappe.throw("Specified entity is not a folder", NotADirectoryError)
    if not parent_is_active:
        frappe.throw("Specified folder has been trashed by the owner")
    if not frappe.session.user == parent_owner:
        frappe.throw("Not permitted")
    if not frappe.has_permission(
        doctype="Drive Entity", doc=entity_name, ptype="write", user=frappe.session.user
    ):
        frappe.throw(
            "Not permitted to read",
            frappe.PermissionError,
        )

    # entity_ancestors = get_ancestors_of("Drive Entity", entity_name)
    # flag = False
    # for z_entity_name in entity_ancestors:
    #    result = frappe.db.exists("Drive Entity", {"name": z_entity_name, "is_active": 0})
    #    if result:
    #        flag = True
    #        break
    # if flag == True:
    #    frappe.throw("Parent Folder has been deleted")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveUser = frappe.qb.DocType("User")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveEntity.owner,
        DriveUser.full_name,
        DriveUser.user_image,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_download,
        DriveEntity.allow_comments,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .left_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .select(*selectedFields)
        .where(
            (DriveEntity.parent_drive_entity == entity_name) & (DriveEntity.is_active == is_active)
        )
        .groupby(DriveEntity.name)
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    result = query.run(as_dict=True)
    for i in result:
        if i.is_group:
            child_count = get_children_count(i.name)
            i["item_count"] = child_count
    return result


@frappe.whitelist()
def get_trashed_entities(order_by="modified", is_active=1):
    return frappe.db.get_all(
        "Drive Entity",
        filters={"is_active": 0, "owner": ["like", frappe.session.user]},
        fields=[
            "name",
            "title",
            "is_group",
            "owner",
            "modified",
            "creation",
            "file_size",
            "file_ext",
            "color",
            "document",
            "mime_type",
        ],
    )


def get_entity(entity_name, fields=None):
    """
    Return specific entity

    :param entity_name: Document-name of the file or folder
    :raises PermissionError: If the user does not have access to the specified entity
    :rtype: frappe._dict
    """
    fields = fields or ["name", "title", "owner"]
    return frappe.db.get_value("Drive Entity", entity_name, fields, as_dict=1)


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
            & (Comment.reference_doctype == "Drive Entity")
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
        doc = frappe.get_doc("Drive Entity", entity)
        if not doc:
            frappe.throw("Entity does not exist", ValueError)
        if move:
            doc.move()
        doc.unshare(frappe.session.user)


def delete_background_job(entity, ignore_permissions):
    frappe.delete_doc("Drive Entity", entity, ignore_permissions=ignore_permissions)


@frappe.whitelist()
def delete_entities(entity_names):
    """
    Delete DriveEntities

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    for entity in entity_names:
        root_entity = get_ancestors_of("Drive Entity", entity)
        if root_entity:
            root_entity = get_ancestors_of("Drive Entity", entity)[0]
        else:
            root_entity = get_user_directory()
        owns_root_entity = frappe.has_permission(
            doctype="Drive Entity",
            doc=root_entity,
            ptype="write",
            user=frappe.session.user,
        )
        has_write_access = frappe.has_permission(
            doctype="Drive Entity", doc=entity, ptype="write", user=frappe.session.user
        )
        ignore_permissions = owns_root_entity or has_write_access
        frappe.db.set_value("Drive Entity", entity, "is_active", -1)
        frappe.enqueue(
            delete_background_job,
            queue="default",
            timeout=None,
            entity=entity,
            ignore_permissions=ignore_permissions,
        )


@frappe.whitelist()
def list_favourites(order_by="modified"):
    """
    Return list of DriveEntity records present in this folder

    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :return: List of DriveEntity records
    :rtype: list
    """

    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    DriveUser = frappe.qb.DocType("User")
    UserGroupMember = frappe.qb.DocType("User Group Member")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveEntity.owner,
        DriveUser.full_name,
        DriveEntity.owner,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.mime_type,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_comments,
        DriveDocShare.read,
        fn.Max(DriveDocShare.write).as_("write"),
        DriveDocShare.share,
        DriveDocShare.everyone,
        DriveFavourite.entity.as_("is_favourite"),
    ]
    query = (
        frappe.qb.from_(DriveEntity)
        .right_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .left_join(DriveDocShare)
        .on((DriveDocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on(
            (
                (UserGroupMember.parent == DriveDocShare.user_name)
                & (UserGroupMember.user == frappe.session.user)
            )
            | (
                (DriveDocShare.user_name == frappe.session.user)
                | ((DriveDocShare.everyone == 1) | (DriveDocShare.public == 1))
            )
        )
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .select(*selectedFields)
        .where(
            (DriveEntity.is_active == 1)
            & ((DriveEntity.owner == frappe.session.user) | (DriveDocShare.read == 1))
        )
        .groupby(DriveEntity.name)
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    return query.run(as_dict=True)


@frappe.whitelist()
def add_or_remove_favourites(entity_names=None, clear_all=False):
    """
    Favouite or unfavourite DriveEntities for specified user

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """

    if clear_all:
        frappe.db.delete("Drive Favourite", {"user": frappe.session.user})
        return

    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)
    for entity in entity_names:
        existing_doc = frappe.db.exists(
            {
                "doctype": "Drive Favourite",
                "entity": entity,
                "user": frappe.session.user,
            }
        )
        if existing_doc:
            frappe.delete_doc("Drive Favourite", existing_doc)
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "Drive Favourite",
                    "entity": entity,
                    "user": frappe.session.user,
                }
            )
            doc.insert()


# def toggle_is_active(doc):
#     doc.is_active = 0 if doc.is_active else 1
#     frappe.db.set_value('Drive Entity', doc.name, 'is_active',doc.is_active)
#     for child in doc.get_children():
#         toggle_is_active(child)


@frappe.whitelist()
def remove_or_restore(entity_names, move=False):
    """
    To move entities to or restore entities from the trash

    :param entity_names: List of document-names
    :type entity_names: list[str]
    """
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
    if not isinstance(entity_names, list):
        frappe.throw(f"Expected list but got {type(entity_names)}", ValueError)

    def depth_zero_toggle_is_active(doc):
        doc.is_active = 0 if doc.is_active else 1
        frappe.db.set_value("Drive Entity", doc.name, "is_active", doc.is_active)

    for entity in entity_names:
        doc = frappe.get_doc("Drive Entity", entity)
        if doc.is_active:
            entity_ancestors = get_ancestors_of("Drive Entity", entity)
            if entity_ancestors:
                doc.parent_before_trash = entity_ancestors[0]
            else:
                doc.parent_before_trash = get_user_directory()
            if move:
                doc.move()

        else:
            parent_is_active = frappe.db.get_value(
                "Drive Entity", doc.parent_before_trash, "is_active"
            )
            if parent_is_active:
                doc.move(doc.parent_before_trash)
            else:
                doc.move()
        depth_zero_toggle_is_active(doc)
        # frappe.enqueue(toggle_is_active,queue="default",timeout=None,doc=doc)


@frappe.whitelist()
def call_controller_method(entity_name, method):
    """
    Call a whitelisted Drive Entity controller method

    :param entity_name: Document-name of the document on which the controller method is to be called
    :param method: The controller method to be called
    :raises ValueError: If the entity does not exist
    :return: The result of the controller method
    """

    drive_entity = frappe.get_doc("Drive Entity", frappe.local.form_dict.pop("entity_name"))
    if not drive_entity:
        frappe.throw("Entity does not exist", ValueError)
    method = frappe.local.form_dict.pop("method")
    drive_entity.is_whitelisted(method)
    frappe.local.form_dict.pop("cmd")
    return drive_entity.run_method(method, **frappe.local.form_dict)


@frappe.whitelist()
def list_recents(order_by="last_interaction"):
    """
    Return list of DriveEntity records present in this folder

    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :return: List of DriveEntity records
    :rtype: list
    """

    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    DriveRecent = frappe.qb.DocType("Drive Entity Log")
    DriveUser = frappe.qb.DocType("User")
    UserGroupMember = frappe.qb.DocType("User Group Member")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveUser.full_name,
        DriveUser.user_image,
        DriveEntity.owner,
        DriveEntity.is_group,
        DriveEntity.file_size,
        DriveEntity.mime_type,
        DriveEntity.allow_comments,
        DriveEntity.allow_download,
        DriveEntity.creation,
        DriveEntity.document,
        DriveFavourite.entity.as_("is_favourite"),
        DriveDocShare.user_name,
        DriveDocShare.read,
        fn.Max(DriveDocShare.write).as_("write"),
        DriveDocShare.share,
        DriveDocShare.everyone,
        DriveRecent.last_interaction.as_("modified"),
    ]
    query = (
        frappe.qb.from_(DriveRecent)
        .left_join(DriveEntity)
        .on(
            (DriveRecent.entity_name == DriveEntity.name)
            & (DriveRecent.user == frappe.session.user)
        )
        .left_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .left_join(DriveDocShare)
        .on((DriveDocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on(
            (
                (UserGroupMember.parent == DriveDocShare.user_name)
                & (UserGroupMember.user == frappe.session.user)
            )
            | (
                (DriveDocShare.user_name == frappe.session.user)
                | ((DriveDocShare.everyone == 1) | (DriveDocShare.public == 1))
            )
        )
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .select(*selectedFields)
        .where(
            (DriveEntity.is_active == 1)
            & ((DriveEntity.owner == frappe.session.user) | (DriveDocShare.read == 1))
        )
        .groupby(DriveEntity.name)
        .orderby(DriveRecent.last_interaction, order=Order.desc)
    )
    return query.run(as_dict=True)


@frappe.whitelist()
def remove_recents(entity_names=None, clear_all=False):
    """
    Clear recent DriveEntities for specified user

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """

    if clear_all:
        frappe.db.delete("Drive Entity Log", {"user": frappe.session.user})
        return
    if isinstance(entity_names, str):
        entity_names = json.loads(entity_names)
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
def get_children_count(drive_entity):
    children_count = frappe.db.count(
        "Drive Entity", {"parent_drive_entity": drive_entity, "is_active": 1}
    )
    return children_count


@frappe.whitelist()
def does_entity_exist(name=None, parent_entity=None):
    result = frappe.db.exists(
        "Drive Entity", {"parent_drive_entity": parent_entity, "title": name}
    )
    return bool(result)


def auto_delete_from_trash():
    days_before = (date.today() - timedelta(days=30)).isoformat()
    result = frappe.db.get_all(
        "Drive Entity",
        filters={"is_active": 0, "trashed_on": ["<", days_before]},
        fields=["name"],
    )
    delete_entities(result)


@frappe.whitelist()
def get_user_directory_size():
    try:
        user_directory = get_user_directory(0)
        cmd = f"du -sh {Path(user_directory.path)} | grep -oP '^[\d.]+[KMG]' "
        result = os.popen(cmd)
        size = result.read().strip()
    except:
        size = "0M"
    return size


@frappe.whitelist()
def toggle_allow_comments(entity_name, new_value):
    """
    Toggle allow comments for entity without updating modified

    """

    frappe.db.set_value(
        "Drive Entity", entity_name, "allow_comments", new_value, update_modified=False
    )
    return


@frappe.whitelist()
def toggle_allow_download(entity_name, new_value):
    """
    Toggle allow download for entity without updating modified

    """

    frappe.db.set_value(
        "Drive Entity", entity_name, "allow_download", new_value, update_modified=False
    )
    return


@frappe.whitelist()
def get_title(entity_name):
    """
    Toggle allow download for entity

    """
    if not frappe.has_permission(
        doctype="Drive Entity", doc=entity_name, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Not permitted", frappe.PermissionError)
    return frappe.db.get_value("Drive Entity", entity_name, "title")
