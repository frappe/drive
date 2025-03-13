import frappe
import os
import re
import mimetypes
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from drive.locks.distributed_lock import DistributedLock
from pathlib import Path
from io import BytesIO


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
        embed = frappe.get_doc("Drive File", embed_name)
        embed_path = embed.path
    except frappe.exceptions.DoesNotExistError:
        embed = frappe.db.get_list(
            "Drive File", filters={"old_name": embed_name.split(".")[0]}, fields=["path"]
        )[0]
        embed_path = embed["path"]

    embed_path = Path(frappe.get_site_path("private/files"), embed_path)

    with open(
        str(embed_path),
        "rb",
    ) as file:
        range_header = frappe.request.headers.get("Range", None)
        if range_header:
            return stream_file_content(embed_path, range_header)
        embed_data = BytesIO(file.read())
        response = Response(
            wrap_file(frappe.request.environ, embed_data),
            direct_passthrough=True,
        )
        response.headers.set("Content-Disposition", "inline", filename=embed_name)
    return response


def stream_file_content(embed_path, range_header):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param drive_entity: Drive Entity record object
    """

    # range_header = frappe.request.headers.get("Range", None)
    size = os.path.getsize(str(embed_path))
    byte1, byte2 = 0, None

    m = re.search("(\d+)-(\d*)", range_header)
    g = m.groups()

    if g[0]:
        byte1 = int(g[0])
    if g[1]:
        byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1

    data = None
    with open(embed_path, "rb") as f:
        f.seek(byte1)
        data = f.read(length)

    res = Response(
        data, 206, mimetype=mimetypes.guess_type(embed_path)[0], direct_passthrough=True
    )
    res.headers.add("Content-Range", "bytes {0}-{1}/{2}".format(byte1, byte1 + length - 1, size))
    return res
