import frappe
import os
from pathlib import Path
from PIL import Image, ImageOps
from io import BytesIO
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from werkzeug.utils import secure_filename
from drive.utils.files import get_user_directory, create_user_directory, get_new_title
from drive.locks.distributed_lock import DistributedLock


@frappe.whitelist()
def create_image_thumbnail(entity_name):
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
        image_path = drive_entity.path
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            image.thumbnail((0.3*width,0.3*height))
            thumbnail_data = BytesIO()
            image.save(thumbnail_data, format="JPEG")
            thumbnail_data.seek(0)
            response = Response(
                wrap_file(frappe.request.environ, thumbnail_data),
                direct_passthrough=True,
            )
            response.headers.set("Content-Type", "image/jpeg")
            response.headers.set(
                "Content-Disposition", "inline", filename=drive_entity.title
            )
            return response
