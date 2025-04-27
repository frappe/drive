import frappe
import os
import re
import mimetypes
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from pathlib import Path
from io import BytesIO
from drive.utils.files import FileManager


@frappe.whitelist()
def get_file_content(embed_name, parent_entity_name):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param trigger_download: 1 to trigger the "Save As" dialog. Defaults to 0
    :type trigger_download: int
    :raises ValueError: If the DriveEntity doc does not exist or is not a file
    :raises PermissionError: If the current user does not have permission to read the file
    :raises FileLockedError: If the file has been writer-locked
    """
    # Used for <v0.1 support
    old_parent_name = frappe.get_list(
        "Drive File",
        {"old_name": parent_entity_name},
        ["name"],
    )
    if old_parent_name:
        parent_entity_name = old_parent_name[0]["name"]

    if not frappe.has_permission(
        doctype="Drive File",
        doc=parent_entity_name,
        ptype="read",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to view this file")

    drive_entity = frappe.get_value(
        "Drive File",
        parent_entity_name,
        ["document", "title", "mime_type", "file_size", "owner", "path", "team"],
        as_dict=1,
    )
    if not drive_entity:
        drive_entity = frappe.get_list(
            "Drive File",
            {"old_name": parent_entity_name},
            fields=["document", "title", "mime_type", "file_size", "owner", "path", "team"],
        )[0]

    if not drive_entity.document:
        raise ValueError

    try:
        embed = frappe.get_doc("Drive File", embed_name.split(".")[0])
        embed_path = embed.path
    except frappe.exceptions.DoesNotExistError:
        embed = frappe.db.get_list(
            "Drive File", filters={"old_name": embed_name.split(".")[0]}, fields=["path"]
        )[0]
        embed_path = embed["path"]

    # Flaw? Doesn't stream for range header
    manager = FileManager()
    embed_data = manager.get_file(embed_path)
    response = Response(
        wrap_file(frappe.request.environ, embed_data),
        direct_passthrough=True,
    )
    response.headers.set("Content-Disposition", "inline", filename=embed_name)
    return response
