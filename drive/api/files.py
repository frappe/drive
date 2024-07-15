import frappe
import os
import re
import json
from pypika import Order, Case, functions as fn
from pathlib import Path
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from werkzeug.utils import secure_filename, send_file
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
from frappe.utils import cint
from drive.api.notifications import notify_mentions
from drive.api.storage import get_storage_allowed


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
    new_title = get_new_title(title, parent, document=True)

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
    drive_entity.file_size = 0
    drive_entity.flags.file_created = True
    drive_entity.save()
    return drive_entity


def create_uploads_directory(user=None):
    user_directory_name = get_user_directory(user).name
    user_directory_uploads_path = Path(
        frappe.get_site_path("private/files"), user_directory_name, "uploads"
    )
    user_directory_uploads_path.mkdir(exist_ok=True)
    return user_directory_uploads_path


def get_user_uploads_directory(user=None):
    user_directory_name = get_user_directory(user).name
    user_directory_uploads_path = Path(
        frappe.get_site_path("private/files"), user_directory_name, "uploads"
    )
    if not os.path.exists(user_directory_uploads_path):
        try:
            user_directory_uploads_path = create_uploads_directory()
        except FileNotFoundError:
            user_directory_uploads_path = create_uploads_directory()
    return user_directory_uploads_path


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
    upload_session = frappe.form_dict.uuid
    title = get_new_title(file.filename, parent)

    current_chunk = int(frappe.form_dict.chunk_index)
    total_chunks = int(frappe.form_dict.total_chunk_count)

    save_path = Path(user_directory.path) / f"{parent}_{secure_filename(title)}"
    temp_path = (
        Path(get_user_uploads_directory(user=frappe.session.user))
        / f"{upload_session}_{secure_filename(title)}"
    )

    if get_storage_allowed() < int(frappe.form_dict.total_file_size):
        frappe.throw("Out of allocated storage", ValueError)

    with temp_path.open("ab") as f:
        f.seek(int(frappe.form_dict.chunk_byte_offset))
        f.write(file.stream.read())
        if not f.tell() >= int(frappe.form_dict.total_file_size):
            return
        else:
            pass

    if current_chunk + 1 == total_chunks:
        file_size = temp_path.stat().st_size
        if file_size != int(frappe.form_dict.total_file_size):
            temp_path.unlink()
            frappe.throw("Size on disk does not match specified filesize", ValueError)
        else:
            os.rename(temp_path, save_path)
        mime_type, _ = mimetypes.guess_type(temp_path)

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
            "path": str(path),
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
        suggested_name = get_new_title(title, parent, folder=True)
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
        ["content", "raw_content", "settings"],
        as_dict=1,
    )
    return drive_document


@frappe.whitelist()
def passive_rename(entity_name, new_title):
    frappe.db.set_value("Drive Entity", entity_name, "title", new_title)
    return new_title


@frappe.whitelist()
def save_doc(entity_name, doc_name, raw_content, content, file_size, mentions, settings=None):
    if not frappe.has_permission(
        doctype="Drive Entity",
        doc=entity_name,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to view this file")
    if settings:
        frappe.db.set_value("Drive Document", doc_name, "settings", json.dumps(settings))
    frappe.db.set_value("Drive Document", doc_name, "content", content)
    frappe.db.set_value("Drive Document", doc_name, "raw_content", raw_content)
    frappe.db.set_value("Drive Document", doc_name, "mentions", json.dumps(mentions))
    frappe.db.set_value("Drive Entity", entity_name, "file_size", file_size)
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
        response.headers.add("Content-Length", str(drive_entity.file_size))
        response.headers.add("Content-Type", response.mimetype)
        response.headers.add("Accept-Range", "bytes")

        if trigger_download:
            response.headers.add(
                "Content-Disposition",
                "attachment",
                filename=format(urllib.parse.quote(drive_entity.title.encode("utf8"))),
            )
            return send_file(
                drive_entity.path,
                mimetype=drive_entity.mime_type,
                as_attachment=True,
                download_name=drive_entity.title,
                environ=frappe.request.environ,
            )

        response.headers.add(
            "Content-Disposition",
            "inline",
            filename=format(urllib.parse.quote(drive_entity.title.encode("utf8"))),
        )
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

    max_length = 20 * 1024 * 1024  # 20 MB in bytes
    if length > max_length:
        length = max_length

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
def list_folder_contents(entity_name=None, order_by="modified", is_active=1, limit=100, offset=0):
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
    parent, parent_is_group, parent_is_active = frappe.db.get_value(
        "Drive Entity", entity_name, ["name", "is_group", "is_active"]
    )
    # Parent can be null for $HOME_DIR
    if parent:
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
        .left_join(DriveDocShare)
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
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
        .where(
            (DriveEntity.parent_drive_entity == entity_name)
            & (DriveEntity.is_active == 1)
            & (
                (UserGroupMember.user == frappe.session.user)
                | (
                    (DriveDocShare.user_name == frappe.session.user)
                    | (DriveDocShare[general_access_val] == 1)
                    | (DriveEntity.owner == frappe.session.user)
                )
            )
        )
        .groupby(DriveEntity.name)
        .orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    result = query.run(as_dict=True)
    return result


@frappe.whitelist()
def list_owned_entities(
    entity_name=None, order_by="modified", is_active=True, limit=100, offset=0
):
    """
    Return list of DriveEntity records present in this folder

    :param entity_name: Document-name of the folder whose contents are to be listed. Defaults to the user directory
    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :raises PermissionError: If the user does not have access to the specified folder
    :return: List of DriveEntity records
    :rtype: list
    """
    is_active = json.loads(is_active)
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
        DriveEntity.is_active,
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
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
        .where(
            (DriveEntity.parent_drive_entity == entity_name) & (DriveEntity.is_active == is_active)
        )
        .groupby(DriveEntity.name)
        .orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
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
def list_trashed_entities(
    entity_name=None, order_by="modified", is_active=True, limit=100, offset=0
):
    """
    Return list of DriveEntity records present in this folder

    :param entity_name: Document-name of the folder whose contents are to be listed. Defaults to the user directory
    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :raises PermissionError: If the user does not have access to the specified folder
    :return: List of DriveEntity records
    :rtype: list
    """
    is_active = json.loads(is_active)
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
        DriveEntity.is_active,
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
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
        .where((DriveEntity.is_active == 0) & (DriveEntity.owner == frappe.session.user))
        .groupby(DriveEntity.name)
        .orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
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
def delete_entities(entity_names=None, clear_all=None):
    """
    Delete DriveEntities

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """
    if clear_all:
        entity_names = frappe.db.get_list(
            "Drive Entity", {"is_active": ["<", "1"], "owner": frappe.session.user}, pluck="name"
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
def list_favourites(order_by="modified", limit=100, offset=0):
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
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
        .where(
            (DriveEntity.is_active == 1)
            & ((DriveEntity.owner == frappe.session.user) | (DriveDocShare.read == 1))
        )
        .groupby(DriveEntity.name)
        .orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
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
        if doc.is_active:
            frappe.db.delete("Drive DocShare", {"share_name": doc.name})
            doc.is_active = 0
        else:
            doc.is_active = 1
            doc.inherit_permissions()

        frappe.db.set_value("Drive Entity", doc.name, "is_active", doc.is_active)

    for entity in entity_names:
        doc = frappe.get_doc("Drive Entity", entity)
        if doc.owner != frappe.session.user:
            raise frappe.PermissionError("You do not have permission to remove this file")
        if doc.is_active:
            entity_ancestors = get_ancestors_of(entity)
            if entity_ancestors:
                doc.parent_before_trash = entity_ancestors[0]
                doc.save()
            else:
                doc.parent_before_trash = get_user_directory()
                doc.save()
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


@frappe.whitelist(allow_guest=True)
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
def list_recents(order_by="last_interaction", limit=100, offset=0):
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
        .offset(offset)
        .limit(limit)
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
        doc = frappe.get_doc("Drive Entity", entity)
        new_parent = new_parent or get_user_directory(doc.owner).name

        if new_parent == doc.parent_drive_entity:
            return doc
        is_group = frappe.db.get_value("Drive Entity", new_parent, "is_group")
        if not is_group:
            raise NotADirectoryError()
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
    result = frappe.db.sql(
        f"""
    SELECT  `tabDrive Entity`.name,
            `tabDrive Entity`.title, 
            `tabDrive Entity`.owner,
            `tabDrive Entity`.mime_type,
            `tabDrive Entity`.is_group,
            `tabDrive Entity`.document,
            `tabDrive Entity`.color,
            `tabUser`.user_image,
            `tabUser`.full_name
    FROM `tabDrive Entity`
    LEFT JOIN `tabDrive DocShare`
    ON `tabDrive DocShare`.`share_name` = `tabDrive Entity`.`name`
    LEFT JOIN `tabUser Group Member`
    ON `tabUser Group Member`.`parent` = `tabDrive DocShare`.`user_name`
    LEFT JOIN `tabUser` ON `tabDrive Entity`.`owner` = `tabUser`.`email`
    WHERE (`tabUser Group Member`.`user` = {user} 
            OR `tabDrive DocShare`.`user_name` = {user} 
            OR `tabDrive DocShare`.`everyone` = 1 
            OR `tabDrive Entity`.`owner` = {user})
        AND `tabDrive Entity`.`is_active` = 1
        AND MATCH(title) AGAINST ({text} IN BOOLEAN MODE)
        AND NOT `tabDrive Entity`.`name` LIKE {omit}
    GROUP  BY `tabDrive Entity`.`name` 
    """,
        as_dict=1,
    )
    return result


@frappe.whitelist()
def generate_upward_path(entity_name):
    """
    Given an ID traverse upwards till the root node
    Stops when parent_drive_entity IS NULL
    """
    # CONCAT_WS('/', t.title, gp.path),
    entity_name = frappe.db.escape(entity_name)
    result = frappe.db.sql(
        f"""
        WITH RECURSIVE generated_path as ( 
        SELECT 
            `tabDrive Entity`.title,
            `tabDrive Entity`.name,
            `tabDrive Entity`.parent_drive_entity,
            `tabDrive Entity`.owner
        FROM `tabDrive Entity` 
        WHERE `tabDrive Entity`.name = {entity_name}

        UNION ALL

        SELECT 
            t.title,
            t.name,
            t.parent_drive_entity,
            t.owner
        FROM generated_path as gp
        JOIN `tabDrive Entity` as t ON t.name = gp.parent_drive_entity) 
        SELECT * FROM generated_path;
    """,
        as_dict=1,
    )
    return result[::-1]


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
            `tabDrive Entity`.name,
            `tabDrive Entity`.parent_drive_entity
        FROM `tabDrive Entity` 
        WHERE `tabDrive Entity`.name = {entity_name}

        UNION ALL

        SELECT 
            t.name,
            t.parent_drive_entity
        FROM generated_path as gp
        JOIN `tabDrive Entity` as t ON t.name = gp.parent_drive_entity) 
        SELECT name FROM generated_path;
    """,
        as_dict=0,
    )
    # Match the output of frappe/nested.py get_ancestors_of
    flattened_list = [item for sublist in result for item in sublist]
    flattened_list.pop(0)
    return flattened_list


@frappe.whitelist(allow_guest=True)
def get_shared_breadcrumbs(share_name):
    """
    given a node return the root. stops when share_parent IS NULL
    given a node and parent travel till
    the child of the parent_entity and append the parent_entity
    """
    # CONCAT_WS('/', t.title, gp.path),
    share_name = frappe.db.escape(share_name)
    result = frappe.db.sql(
        f"""
        WITH RECURSIVE generated_path as ( 
        SELECT 
            `tabDrive DocShare`.name,
            `tabDrive DocShare`.share_name,
            `tabDrive DocShare`.share_parent
        FROM `tabDrive DocShare` 
        WHERE `tabDrive DocShare`.name = {share_name}

        UNION ALL

        SELECT 
            `tabDrive DocShare`.name,
            `tabDrive DocShare`.share_name,
            `tabDrive DocShare`.share_parent
        FROM generated_path as gp
        JOIN `tabDrive DocShare` ON `tabDrive DocShare`.name = gp.share_parent
        ) 
        SELECT * FROM generated_path;
    """,
        as_dict=1,
    )
    share_breadcrumbs = []
    for i in result:
        share_breadcrumbs.append(
            frappe.get_value(
                "Drive Entity",
                i.share_name,
                ["name", "title", "parent_drive_entity", "owner"],
                as_dict=1,
            )
        )
    return share_breadcrumbs[::-1]
