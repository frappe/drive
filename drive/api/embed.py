import frappe
import os
import re
import magic
import mimetypes
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file
from drive.locks.distributed_lock import DistributedLock
from pathlib import Path
from io import BytesIO
from drive.utils.files import get_user_directory
from drive.api.files import create_drive_entity


def create_user_embeds_directory(user=None):
    user_directory_name = get_user_directory(user).name
    user_directory_embeds_path = Path(
        frappe.get_site_path("private/files"), user_directory_name, "embeds"
    )
    user_directory_embeds_path.mkdir(exist_ok=True)
    return user_directory_embeds_path


def get_user_embeds_directory(user=None):
    user_directory_name = get_user_directory(user).name
    user_directory_embeds_path = Path(
        frappe.get_site_path("private/files"), user_directory_name, "embeds"
    )
    if not os.path.exists(user_directory_embeds_path):
        try:
            user_directory_embeds_path = create_user_embeds_directory()
        except FileNotFoundError:
            user_directory_embeds_path = create_user_embeds_directory()
    return user_directory_embeds_path


@frappe.whitelist()
def upload_chunked_file(fullpath=None, parent=None, last_modified=None):
    """
    Accept chunked file contents via a multipart upload, store the file on
    disk, and insert a corresponding DriveEntity doc.

    :param fullpath: Full path of the uploaded file
    :param parent: Document-name of the parent folder. Defaults to the user directory
    :raises PermissionError: If the user does not have write access to the specified parent folder
    :raises FileExistsError: If a file with the same name already exists in the specified parent folder
    :raises ValueError: If the size of the stored file does not match the specified filesize
    :return: DriveEntity doc once the entire file has been uploaded
    """

    parent = frappe.form_dict.parent
    drive_entity = frappe.get_value(
        "Drive Entity",
        parent,
        ["document", "title", "mime_type", "file_size", "owner"],
        as_dict=1,
    )
    try:
        embed_directory = get_user_embeds_directory(user=drive_entity.owner)
    except FileNotFoundError:
        embed_directory = create_user_embeds_directory(user=drive_entity.owner)
    embed_directory = Path(
        frappe.get_site_path("private/files"),
        get_user_directory(user=drive_entity.owner).name,
        "embeds",
    )
    if not frappe.has_permission(
        doctype="Drive Entity", doc=parent, ptype="write", user=frappe.session.user
    ):
        frappe.throw("Cannot upload due to insufficient permissions", frappe.PermissionError)

    file = frappe.request.files["file"]

    name = frappe.form_dict.uuid
    title, file_ext = os.path.splitext(frappe.form_dict.file_name)
    mime_type = frappe.form_dict.mime_type
    current_chunk = int(frappe.form_dict.chunk_index)
    total_chunks = int(frappe.form_dict.total_chunk_count)
    file_size = int(frappe.form_dict.total_file_size)
    save_path = Path(embed_directory) / f"{secure_filename(name+file_ext)}"
    if current_chunk == 0 and save_path.exists():
        frappe.throw(f"File '{title}' already exists", FileExistsError)

    if not mime_type:
        mime_type = magic.from_buffer(open(save_path, "rb").read(2048), mime=True)

    with save_path.open("ab") as f:
        f.seek(int(frappe.form_dict.chunk_byte_offset))
        f.write(file.stream.read())

    if current_chunk + 1 == total_chunks:
        file_size = save_path.stat().st_size

    if file_size != int(frappe.form_dict.total_file_size):
        save_path.unlink()
        frappe.throw("Size on disk does not match specified filesize", ValueError)
    drive_entity = create_drive_entity(
        name, title, parent, save_path, file_size, file_ext, mime_type, last_modified
    )
    return str(name + file_ext)


@frappe.whitelist(allow_guest=True)
def get_file_content(embed_name, parent_entity_name, trigger_download=0):
    """
    Stream file content and optionally trigger download

    :param entity_name: Document-name of the file whose content is to be streamed
    :param trigger_download: 1 to trigger the "Save As" dialog. Defaults to 0
    :type trigger_download: int
    :raises ValueError: If the DriveEntity doc does not exist or is not a file
    :raises PermissionError: If the current user does not have permission to read the file
    :raises FileLockedError: If the file has been writer-locked
    """
    drive_entity = frappe.get_value(
        "Drive Entity",
        parent_entity_name,
        ["document", "title", "mime_type", "file_size", "owner"],
        as_dict=1,
    )
    if not drive_entity.document:
        raise ValueError

    is_public = False
    if frappe.db.exists(
        {
            "doctype": "Drive DocShare",
            "share_doctype": "Drive Entity",
            "share_name": parent_entity_name,
            "public": 1,
        }
    ):
        is_public = True
    if not is_public:
        if not frappe.has_permission(
            doctype="Drive Entity",
            doc=parent_entity_name,
            ptype="read",
            user=frappe.session.user,
        ):
            raise frappe.PermissionError("You do not have permission to view this file")

    with DistributedLock(drive_entity.path, exclusive=False):
        user_embeds_directory = get_user_embeds_directory(user=drive_entity.owner)
        embed_path = Path(user_embeds_directory, embed_name)
        with open(str(embed_path), "rb") as file:
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
