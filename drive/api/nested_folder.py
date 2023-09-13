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


@frappe.whitelist()
def get_children_count(drive_entity):
    children_count = frappe.db.count("Drive Entity", {"parent_drive_entity": drive_entity})
    return children_count


@frappe.whitelist()
def folder_contents(entity_name=None, order_by="modified", is_active=1):
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
        result = frappe.db.exists("Drive Entity", {"name": z_entity_name, "is_active": 0})
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
        DriveEntity.file_ext,
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
            (DriveEntity.parent_drive_entity == entity_name) & (DriveEntity.is_active == is_active)
        )
        .groupby(DriveEntity.name)
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    result = query.run(as_dict=True)
    return result
