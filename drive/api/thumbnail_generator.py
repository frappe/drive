import frappe
import os
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
from frappe.utils.nestedset import rebuild_tree, get_ancestors_of
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from werkzeug.utils import secure_filename
from drive.utils.files import get_user_directory, create_user_directory, get_new_title
from drive.locks.distributed_lock import DistributedLock
from drive.utils.files import (
    get_user_directory,
    create_user_directory,
    get_new_title,
    get_user_thumbnails_directory,
    create_user_thumbnails_directory,
    create_thumbnail,
)

@frappe.whitelist(allow_guest=True)
def create_image_thumbnail(entity_name):
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["is_group", "path", "title", "mime_type", "file_size"],
        as_dict=1,
    )
    if not drive_entity or drive_entity.is_group:
        raise ValueError
    entity_ancestors = get_ancestors_of("Drive Entity", entity_name)
    flag = False
    for z_entity_name in entity_ancestors:
        result = frappe.db.exists(
            {
                "doctype": "DocShare",
                "share_doctype": "Drive Entity",
                "share_name": z_entity_name,
                "everyone": 1,
            }
        )
        if result:
            flag = True
            break
    if not flag:
        if not frappe.has_permission(
            doctype="Drive Entity",
            doc=entity_name,
            ptype="read",
            user=frappe.session.user,
        ):
            raise frappe.PermissionError("You do not have permission to view this file")
    with DistributedLock(drive_entity.path, exclusive=False):
        if frappe.cache().exists(entity_name):
            cached_thumbnbail = frappe.cache().get_value(entity_name)
            response = Response(
                wrap_file(frappe.request.environ, cached_thumbnbail),
                direct_passthrough=True,
            )
            response.headers.set("Content-Type", "image/jpeg")
            response.headers.set("Content-Disposition", "inline", filename=entity_name)
        else:
            user_thumbnails_directory = get_user_thumbnails_directory()
            thumbnail_getpath = Path(user_thumbnails_directory, entity_name)
            with open(str(thumbnail_getpath) + ".thumbnail", "rb") as file:
                thumbnail_data = BytesIO(file.read())
            response = Response(
                wrap_file(frappe.request.environ, thumbnail_data),
                direct_passthrough=True,
            )
            response.headers.set("Content-Type", "image/jpeg")
            response.headers.set("Content-Disposition", "inline", filename=entity_name)
            frappe.cache().set_value(
                entity_name,thumbnail_data
            )
        return response


@frappe.whitelist(allow_guest=True)
def create_video_thumbnail(entity_name):
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["is_group", "path", "title", "mime_type", "file_size"],
        as_dict=1,
    )
    if not drive_entity or drive_entity.is_group:
        raise ValueError
    entity_ancestors = get_ancestors_of("Drive Entity", entity_name)
    flag = False
    for z_entity_name in entity_ancestors:
        result = frappe.db.exists(
            {
                "doctype": "DocShare",
                "share_doctype": "Drive Entity",
                "share_name": z_entity_name,
                "everyone": 1,
            }
        )
        if result:
            flag = True
            break
    if not flag:
        if not frappe.has_permission(
            doctype="Drive Entity",
            doc=entity_name,
            ptype="read",
            user=frappe.session.user,
        ):
            raise frappe.PermissionError("You do not have permission to view this file")
    with DistributedLock(drive_entity.path, exclusive=False):
        if frappe.cache().exists(entity_name):
            cached_thumbnbail = frappe.cache().get_value(entity_name)
            response = Response(
                wrap_file(frappe.request.environ, cached_thumbnbail),
                direct_passthrough=True,
            )
            response.headers.set("Content-Type", "image/jpeg")
            response.headers.set("Content-Disposition", "inline", filename=entity_name)
        else:
            user_thumbnails_directory = get_user_thumbnails_directory()
            thumbnail_getpath = Path(user_thumbnails_directory, entity_name)
            with open(str(thumbnail_getpath) + ".thumbnail", "rb") as file:
                thumbnail_data = BytesIO(file.read())
            response = Response(
                wrap_file(frappe.request.environ, thumbnail_data),
                direct_passthrough=True,
            )
            response.headers.set("Content-Type", "image/jpeg")
            response.headers.set("Content-Disposition", "inline", filename=entity_name)
            frappe.cache().set_value(
                entity_name,thumbnail_data
            )
        return response
