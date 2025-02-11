import frappe
from pathlib import Path
from io import BytesIO
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from drive.locks.distributed_lock import DistributedLock
from drive.utils.files import get_team_thumbnails_directory


@frappe.whitelist(allow_guest=True)
def create_image_thumbnail(entity_name):
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["is_group", "path", "title", "mime_type", "file_size", "owner", "team"],
        as_dict=1,
    )
    if not drive_entity or drive_entity.is_group:
        frappe.throw("No such image found", ValueError)
    if not frappe.has_permission(
        doctype="Drive Entity", doc=drive_entity.name, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Cannot upload due to insufficient permissions", frappe.PermissionError)
    with DistributedLock(drive_entity.path, exclusive=False):
        if frappe.cache().exists(entity_name):
            thumbnail_data = frappe.cache().get_value(entity_name)
        else:
            thumbnail_getpath = Path(get_team_thumbnails_directory(drive_entity.team), entity_name)
            with open(str(thumbnail_getpath) + ".thumbnail", "rb") as file:
                thumbnail_data = BytesIO(file.read())
            frappe.cache().set_value(entity_name, thumbnail_data)

        response = Response(
            wrap_file(frappe.request.environ, thumbnail_data),
            direct_passthrough=True,
        )
        response.headers.set("Content-Type", "image/jpeg")
        response.headers.set("Content-Disposition", "inline", filename=entity_name)
        return response


@frappe.whitelist(allow_guest=True)
def create_video_thumbnail(entity_name):
    drive_entity = frappe.get_value(
        "Drive Entity",
        entity_name,
        ["is_group", "path", "title", "mime_type", "file_size", "owner"],
        as_dict=1,
    )
    if not drive_entity or drive_entity.is_group:
        raise ValueError
    if not frappe.has_permission(
        doctype="Drive Entity", doc=drive_entity.name, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Cannot upload due to insufficient permissions", frappe.PermissionError)
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
            user_thumbnails_directory = get_team_thumbnails_directory(drive_entity.team)
            thumbnail_getpath = Path(user_thumbnails_directory, entity_name)
            with open(str(thumbnail_getpath) + ".thumbnail", "rb") as file:
                thumbnail_data = BytesIO(file.read())
            response = Response(
                wrap_file(frappe.request.environ, thumbnail_data),
                direct_passthrough=True,
            )
            response.headers.set("Content-Type", "image/jpeg")
            response.headers.set("Content-Disposition", "inline", filename=entity_name)
            frappe.cache().set_value(entity_name, thumbnail_data)
        return response
