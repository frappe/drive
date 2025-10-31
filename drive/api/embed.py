from io import BytesIO
from pathlib import Path

import frappe
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

from drive.api.permissions import user_has_permission
from drive.api.files import get_file_internal
from drive.utils import get_home_folder
from drive.utils.files import FileManager


@frappe.whitelist(allow_guest=True)
def get_file_content(embed_name, parent_entity_name):
    """
    Give or stream embed content
    """
    # Used for <v0.1 support, also a security flaw
    old_parent_name = frappe.get_value(
        "Drive File",
        {"old_name": parent_entity_name},
        "name",
    )
    if old_parent_name:
        parent_entity_name = old_parent_name

    if not user_has_permission(parent_entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    drive_entity = frappe.get_value(
        "Drive File",
        parent_entity_name,
        ["document", "title", "mime_type", "file_size", "owner", "path", "team"],
        as_dict=1,
    )

    if not drive_entity.document:
        frappe.throw("This is not an embed.")

    embed = frappe.get_cached_doc("Drive File", embed_name)
    # Remove at some point
    if not embed.path:
        embed = frappe._dict(
            path=str(
                Path(
                    get_home_folder(embed.team)["path"],
                    "embeds",
                    embed_name,
                )
            ),
            team=embed.team,
        )
    return get_file_internal(embed)
