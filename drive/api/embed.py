from pathlib import Path

import frappe

from drive.api.permissions import user_has_permission
from drive.api.files import get_file_internal
from drive.utils import WRITER_CONTENT_DOCTYPE, get_home_folder


@frappe.whitelist(allow_guest=True)
def get_file_content(embed_name: str, parent_entity_name: str):
    """
    Give or stream embed content
    """
    parent = frappe.get_value(
        "File",
        parent_entity_name,
        ["content_doctype", "file_name", "mime_type", "file_size", "owner", "file_url", "team"],
        as_dict=1,
    )

    if parent.content_doctype != WRITER_CONTENT_DOCTYPE:
        frappe.throw("This is not an embed.")

    embed = frappe.get_cached_doc("File", embed_name)

    if embed.folder != parent_entity_name or not user_has_permission(embed_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    if not embed.file_url:
        embed = frappe._dict(
            file_url=str(
                Path(
                    get_home_folder(embed.team)["file_url"],
                    "embeds",
                    embed_name,
                )
            ),
            team=embed.team,
            file_name=embed.file_name,
        )
    return get_file_internal(embed)
