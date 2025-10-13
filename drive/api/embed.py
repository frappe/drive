from io import BytesIO
from pathlib import Path

import frappe
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

from drive.api.permissions import user_has_permission
from drive.utils import get_home_folder
from drive.utils.files import FileManager


@frappe.whitelist(allow_guest=True)
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
    # Used for <v0.1 support, also a security flaw
    old_parent_name = frappe.get_list(
        "Drive File",
        {"old_name": parent_entity_name},
        ["name"],
    )
    if old_parent_name:
        parent_entity_name = old_parent_name[0]["name"]

    if not user_has_permission(parent_entity_name, "read"):
        raise frappe.PermissionError("You do not have permission to view this file")

    cache_key = "embed-" + embed_name
    embed_data = None
    if frappe.cache().exists(cache_key):
        embed_data = frappe.cache().get_value(cache_key)
    if not embed_data:
        drive_entity = frappe.get_value(
            "Drive File",
            parent_entity_name,
            ["document", "title", "mime_type", "file_size", "owner", "path", "team"],
            as_dict=1,
        )

        if not drive_entity:
            drive_entity = frappe.get_list(
                "Drive File",
                filters={"old_name": parent_entity_name},
                fields=["document", "title", "mime_type", "file_size", "owner", "path", "team"],
            )[0]

        if not drive_entity.document:
            raise ValueError
        embed = frappe.get_cached_doc("Drive File", embed_name)
        # Remove at some point
        if not embed.path:
            embed = frappe._dict(
                path=str(
                    Path(
                        get_home_folder(drive_entity.team)["path"],
                        "embeds",
                        embed_name,
                    )
                ),
                team=embed.team,
            )
        # Flaw? Doesn't stream for range header
        manager = FileManager()
        # TBD - redo
        embed_data = BytesIO(manager.get_file(embed).read())
        frappe.cache().set_value(cache_key, (embed_data))

    response = Response(
        wrap_file(frappe.request.environ, embed_data),
        direct_passthrough=True,
    )
    response.headers.set("Content-Disposition", "inline", filename=embed_name)
    return response
