# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
import os
from frappe.utils.nestedset import rebuild_tree, get_ancestors_of
from pypika import Order, functions as fn
from pathlib import Path
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from werkzeug.utils import secure_filename
import uuid
import mimetypes
import hashlib
import json
from drive.utils.files import get_user_directory, create_user_directory, get_new_title
from drive.locks.distributed_lock import DistributedLock
from datetime import date, timedelta

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
    return hashlib.md5(user.encode("utf-8")).hexdigest()


@frappe.whitelist()
def create_document_entity(title, content, parent=None):
    try:
        user_directory = get_user_directory()
    except FileNotFoundError:
        user_directory = create_user_directory()
    new_title = get_new_title(title, parent)

    parent = frappe.form_dict.parent or user_directory.name

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

    if parent == user_directory.name:
        drive_entity.share(frappe.session.user, write=1, share=1)
    return drive_entity


@frappe.whitelist()
def upload_file(fullpath=None, parent=None):
    """
    Accept chunked file contents via a multipart upload, store the file on
    disk, and insert a corresponding DriveEntity doc.

    :param file: Request object containing uploaded chunks
    :param parent: Document-name of the parent folder. Defaults to the user directory
    :param chunk_index: Index of chunk present in the current upload request
    :param total_chunk_count: Total number of chunks for the file
    :param chunk_byte_offset: Position in the file at which the current chunk starts
    :param total_file_size: Total size of the file in bytes
    :raises PermissionError: If the user does not have write access to the specified parent folder
    :raises FileExistsError: If a file with the same name already exists in the specified parent folder
    :raises ValueError: If the size of the stored file does not match the specified filesize
    :return: DriveEntity doc once entire file has been uploaded
    """

    file = frappe.request.files["file"]
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
        frappe.throw(
            "Cannot upload to this folder due to insufficient permissions",
            frappe.PermissionError,
        )

    title = get_new_title(file.filename, parent)

    current_chunk = int(frappe.form_dict.chunk_index)
    total_chunks = int(frappe.form_dict.total_chunk_count)
    save_path = Path(user_directory.path) / f"{parent}_{secure_filename(title)}"

    if current_chunk == 0 and save_path.exists():
        frappe.throw(f"File '{title}' already exists", FileExistsError)
    with open(save_path, "ab") as f:
        f.seek(int(frappe.form_dict.chunk_byte_offset))
        f.write(file.stream.read())

    if current_chunk + 1 == total_chunks:
        file_size = save_path.stat().st_size
        if file_size != int(frappe.form_dict.total_file_size):
            save_path.unlink()
            frappe.throw(
                "Size on disk does not match the specified filesize", ValueError
            )
        else:
            mime_type, encoding = mimetypes.guess_type(save_path)
            file_name, file_ext = os.path.splitext(title)
            name = uuid.uuid4().hex
            path = save_path.parent / f"{name}{save_path.suffix}"
            save_path.rename(path)
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
            # frappe.local.rollback_observers.append(drive_entity)
            drive_entity.insert()

            if parent == user_directory.name:
                drive_entity.share(frappe.session.user, write=1, share=1)

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
        suggested_name = get_new_title(title,parent)
        frappe.throw(f"Folder '{title}' already exists.\n Suggested: {suggested_name}", FileExistsError)

    drive_entity = frappe.get_doc(
        {
            "doctype": "Drive Entity",
            "name": uuid.uuid4().hex,
            "title": title,
            "is_group": 1,
            "parent_drive_entity": parent,
            "color": "#98A1A9",
        }
    )
    drive_entity.insert()

    if parent == user_directory.name:
        drive_entity.share(frappe.session.user, write=1, share=1)

    return drive_entity


@frappe.whitelist()
def get_doc_content(entity_name, trigger_download=0):
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["title", "document", "document.content", "mime_type", "file_size"],
        as_dict=1,
    )
    return drive_entity


""" @frappe.whitelist()
def rename_doc_entity(entity_name, title):
    doc_name = frappe.db.get_value("Drive Entity", entity_name, "document")
    frappe.db.set_value("Drive Document", doc_name, "title", title)
    frappe.db.set_value("Drive Entity", entity_name, "title", title)
    return """


@frappe.whitelist()
def save_doc(entity_name, doc_name, content):
    drive_document = frappe.get_doc("Drive Document", doc_name)
    drive_document.content = content
    drive_document.save()
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

    if frappe.session.user == "Guest":
        frappe.set_user("Administrator")

    trigger_download = int(trigger_download)
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["is_group", "path", "title", "mime_type", "file_size"],
        as_dict=1,
    )
    if not drive_entity or drive_entity.is_group:
        raise ValueError
    if not frappe.has_permission(
        doctype="Drive Entity", doc=entity_name, ptype="read", user=frappe.session.user
    ):
        raise frappe.PermissionError("You do not have permission to view this file")
    with DistributedLock(drive_entity.path, exclusive=False):
        file = open(drive_entity.path, "rb")
        response = Response(
            wrap_file(frappe.request.environ, file), direct_passthrough=True
        )
        response.mimetype = drive_entity.mime_type or "application/octet-stream"
        content_dispostion = "attachment" if trigger_download else "inline"
        response.headers.add(
            "Content-Disposition",
            content_dispostion,
            filename=drive_entity.title.encode("utf-8"),
        )
        response.headers.add("Content-Length", str(drive_entity.file_size))
        return response


@frappe.whitelist()
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
    if not frappe.has_permission(
        doctype="Drive Entity", doc=entity_name, ptype="read", user=frappe.session.user
    ):
        frappe.throw(
            "Cannot access folder due to insufficient permissions",
            frappe.PermissionError,
        )
    entity_ancestors = get_ancestors_of("Drive Entity", entity_name)
    flag = False
    for z_entity_name in entity_ancestors:
        result = frappe.db.exists("Drive Entity", {"name":z_entity_name,"is_active": 0})
        if result:
            flag = True
            break
    if flag == True:
        frappe.throw("Parent Folder has been deleted")                     
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    DocShare = frappe.qb.DocType("DocShare")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveEntity.owner,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_comments,
        DocShare.read,
        fn.Max(DocShare.write).as_("write"),
        DocShare.everyone,
        DocShare.share,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .inner_join(DocShare)
        .on(
            (DocShare.share_name == DriveEntity.name)
            & ((DocShare.user == frappe.session.user) | (DocShare.everyone == 1))
        )
        .left_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .select(*selectedFields)
        .where(
            (DriveEntity.parent_drive_entity == entity_name)
            & (DriveEntity.is_active == is_active)
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
def get_entity(entity_name, fields=None):
    """
    Return specific entity

    :param entity_name: Document-name of the file or folder
    :raises PermissionError: If the user does not have access to the specified entity
    :rtype: frappe._dict
    """

    if not frappe.has_permission(
        doctype="Drive Entity", doc=entity_name, ptype="read", user=frappe.session.user
    ):
        frappe.throw(
            "Cannot access path due to insufficient permissions", frappe.PermissionError
        )
    fields = fields or ["name", "title", "owner"]
    return frappe.db.get_value("Drive Entity", entity_name, fields, as_dict=1)


@frappe.whitelist()
def get_entities_in_path(entity_name, fields=None, shared=False):
    """
    Return list of all DriveEntities present in the path.

    :param entity_name: Document-name of the file or folder
    :param fields: List of doc-fields that should be returned. Defaults to ['name', 'title', 'owner']
    :param shared: True if entity in question has been shared with the user
    :raises PermissionError: If the user does not have access to the specified entity
    :return: List of parents followed by the specified DriveEntity
    :rtype: list[frappe._dict]
    """

    fields = fields or ["name", "title", "owner"]
    rebuild_tree("Drive Entity", "parent_drive_entity")
    if not frappe.has_permission(
        doctype="Drive Entity", doc=entity_name, ptype="read", user=frappe.session.user
    ):
        frappe.throw(
            "Cannot access path due to insufficient permissions", frappe.PermissionError
        )
    path = get_ancestors_of("Drive Entity", entity_name, "lft asc")
    path.append(entity_name)
    entities = [
        frappe.db.get_value("Drive Entity", entity, fields, as_dict=True)
        for entity in path
    ]

    if entities[0].owner != frappe.session.user:
        return get_shared_entities_in_path(entities)

    result = {"is_shared": False, "entities": []}
    result["entities"] += entities
    return result


@frappe.whitelist()
def get_shared_entities_in_path(entities):
    """
    Return list of all DriveEntities present in the path for a shared folder.

    :param entities: All entities in path
    :return: List of parents followed by the specified DriveEntity
    :rtype: list[frappe._dict]
    """

    shared_entities = [entities[-1]]
    highest_level_reached = False
    i = -2
    while not highest_level_reached:
        if frappe.db.exists(
            "DocShare", {"user": frappe.session.user, "share_name": entities[i].name}
        ) or frappe.db.exists(
            "DocShare", {"everyone": 1, "share_name": entities[i].name}
        ):
            shared_entities.insert(0, entities[i])
            i -= 1
        else:
            highest_level_reached = True

    result = {"is_shared": True, "entities": []}
    result["entities"] += shared_entities
    return result


@frappe.whitelist(allow_guest=True)
def list_entity_comments(entity_name):
    if frappe.session.user == "Guest":
        frappe.set_user("Administrator")

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
        .orderby(Comment.creation, order=Order.desc)
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


def delete_background_job(entity,ignore_permissions):
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
        frappe.db.set_value("Drive Entity",entity, "is_active",-1)
        frappe.enqueue(delete_background_job,queue="default",timeout=None,entity=entity,ignore_permissions=ignore_permissions)


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
    DocShare = frappe.qb.DocType("DocShare")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveEntity.owner,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.mime_type,
        DriveEntity.color,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_comments,
        DocShare.read,
        fn.Max(DocShare.write).as_("write"),
        DocShare.share,
        DocShare.everyone,
    ]
    query = (
        frappe.qb.from_(DriveEntity)
        .inner_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .left_join(DocShare)
        .on(
            (DocShare.share_name == DriveEntity.name)
            & ((DocShare.user == frappe.session.user) | (DocShare.everyone == 1))
        )
        .select(*selectedFields)
        .where((DriveEntity.is_active == 1) & (DocShare.read == 1))
        .groupby(DriveEntity.name)
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    return query.run(as_dict=True)


@frappe.whitelist()
def add_or_remove_favourites(entity_names):
    """
    Favouite or unfavourite DriveEntities for specified user

    :param entity_names: List of document-names
    :type entity_names: list[str]
    :raises ValueError: If decoded entity_names is not a list
    """

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
            doc.move()

        else:
            parent_is_active = frappe.db.get_value(
                "Drive Entity", doc.parent_before_trash, "is_active"
            )
            if parent_is_active:
                doc.move(doc.parent_before_trash)
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

    drive_entity = frappe.get_doc(
        "Drive Entity", frappe.local.form_dict.pop("entity_name")
    )
    if not drive_entity:
        frappe.throw("Entity does not exist", ValueError)
    method = frappe.local.form_dict.pop("method")
    drive_entity.is_whitelisted(method)
    frappe.local.form_dict.pop("cmd")
    return drive_entity.run_method(method, **frappe.local.form_dict)


@frappe.whitelist()
def get_children_count(drive_entity):
    children_count = frappe.db.count(
        "Drive Entity", {"parent_drive_entity": drive_entity}
    )
    return children_count


@frappe.whitelist()
def does_entity_exist(name=None, parent_entity=None):
    result = frappe.db.exists(
        "Drive Entity", {"parent_drive_entity": parent_entity, "title": name}
    )
    return bool(result)



def auto_delete_from_trash():
    days_before = (date.today()-timedelta(days=30)).isoformat()
    result = frappe.db.get_all('Drive Entity',
                               filters={ 'is_active': 0, 'trashed_on': ['<',days_before]},
                               fields=['name'])
    delete_entities(result)
