import os
import frappe
from datetime import datetime, timedelta
import uuid
import mimetypes
import json
import base64
import magic
from pathlib import Path
from frappe.utils import get_site_path
from frappe.utils import cint
from werkzeug.wrappers import Response
from werkzeug.utils import secure_filename
from drive.api.files import (
    get_user_directory,
    create_drive_entity,
)
from drive.utils.files import create_thumbnail


@frappe.whitelist(allow_guest=True, methods=["PATCH", "HEAD", "POST", "GET" "OPTIONS", "GET"])
def handle_tus_request(fileID=None):
    tus_version = "1.0.0"
    tus_checksum_algorithm = "md5,sha1,crc32"
    tus_extension = "creation,creation-defer-length,creation-with-upload,expiration,termination"
    current_site_url = frappe.utils.get_url() + "/api/method/drive.api.upload.handle_tus_request"

    # Lowest is 20MB
    # Read site.config to check if bigger payload size is allowed
    max_size = 20 * 1024 * 1024  # 20MB
    expiry = 259200  # 3 days

    response = Response(frappe.request.environ)

    if frappe.request.method == "HEAD":
        """
        Fetch information about a prior upload and get the offset head
        """
        meta = frappe.cache.exists(f"drive_{fileID}")
        if meta is None:
            response.status_code = 404
            return
        response.headers.add("Tus-Extension", tus_extension)
        response.headers.add("Tus-Resumable", tus_version)
        response.headers.add("Tus-Version", tus_version)
        response.headers.add("Tus-Max-Size", str(max_size))
        response.headers.add(
            "Upload-Offset", str(frappe.cache.hget(f"drive_{fileID}", "upload_offset"))
        )
        response.headers.add("Upload-Length", str(frappe.cache.hget(f"drive_{fileID}", "size")))
        response.headers.add("Content-Length", str(frappe.cache.hget(f"drive_{fileID}", "size")))
        response.status_code = 200
        return response

    if frappe.request.method == "POST":
        """
        pre-init/preflight checks(perms, server availability)
        check if file/folder exists in the specified parent already
        create parent folders if webkitRelativePath/fullPath
        init an upload session, process the metadata
        """
        init_file_id = str(uuid.uuid4())
        upload_metadata = frappe.request.headers.get("Upload-Metadata")
        upload_length = frappe.request.headers.get("Upload-Length")
        temp_path = Path(
            frappe.get_site_path(
                "private/files/",
                get_user_directory(user=frappe.session.user).name,
                "uploads",
                init_file_id,
            )
        )

        # Parse metadata
        metadata = {}
        if upload_metadata is not None and upload_metadata != "":
            for kv in upload_metadata.split(","):
                key, value = kv.rsplit(" ", 1)
                decoded_value = base64.b64decode(value.strip()).decode("utf-8")
                metadata[key.strip()] = decoded_value

        metadata.update(size=upload_length)
        metadata.update(date_expiry=datetime.now() + timedelta(seconds=expiry))
        metadata.update(upload_offset=0)
        metadata.update(upload_temp_path=temp_path)

        # todo: reduce extra loop?
        for key, value in metadata.items():
            frappe.cache.hset(f"drive_{init_file_id}", key, value)

        frappe.cache.expire(f"drive_{init_file_id}", expiry)
        response.status_code = 201
        response.headers.add("Location", str(current_site_url + "?fileID=" + init_file_id))
        response.headers.add("Tus-Max-Size", str(max_size))
        return response

    if frappe.request.method == "PATCH":
        """
        write to file based on offset header
        read magic bytes to validate type
        create drive_entity
        create thumbnail if video/image
        """

        meta = frappe.cache.exists(f"drive_{fileID}")
        if meta is None:
            response.status_code = 404
            return
        response.status_code = 200
        file = frappe.request.data
        offset_counter = frappe.cache.hget(f"drive_{fileID}", "upload_offset")
        temp_path = frappe.cache.hget(f"drive_{fileID}", "upload_temp_path")

        # potentially add concat here for multithreading
        # create a file for each chunk
        # recreate the file from unordered but complete chunks that are split up into different temp files
        # will most likely need chunksumming on the client (web crypto api)
        with temp_path.open("ab") as f:
            for chunk in frappe.request.stream:
                if len(chunk) == 0:
                    return None
                f.write(chunk)
                offset_counter += len(chunk)
                frappe.cache.hset(f"drive_{fileID}", "upload_offset", offset_counter)
            f.close()

        if str(offset_counter) == frappe.cache.hget(f"drive_{fileID}", "size"):
            name = str(uuid.uuid4().hex)
            title = frappe.cache.hget(f"drive_{fileID}", "name")
            mime_type = magic.from_buffer(open(temp_path, "rb").read(2048), mime=True)
            _, file_ext = os.path.splitext(title)
            if not file_ext:
                file_ext = mimetypes.guess_extension(mime_type)
            file_name = name + file_ext
            file_size = frappe.cache.hget(f"drive_{fileID}", "size")
            last_modified = frappe.cache.hget(f"drive_{fileID}", "lastModified")
            parent = frappe.cache.hget(f"drive_{fileID}", "fileParent")
            if not parent:
                parent = get_user_directory().name
            save_path = Path(get_user_directory().path) / f"{secure_filename(file_name)}"
            os.rename(temp_path, save_path)
            create_drive_entity(
                name, title, parent, save_path, file_size, file_ext, mime_type, last_modified
            )
            if mime_type.startswith(("image", "video")):
                frappe.enqueue(
                    create_thumbnail,
                    queue="default",
                    timeout=None,
                    now=True,
                    at_front=True,
                    # will set to false once reactivity in new UI is solved
                    entity_name=name,
                    path=save_path,
                    mime_type=mime_type,
                )
            frappe.cache.delete(f"drive_{fileID}")

        response.headers.add("Upload-Offset", offset_counter)
        return response

    if (
        frappe.request.method == "OPTIONS"
        and frappe.request.headers.get("Access-Control-Request-Method", None) is not None
    ):
        """
        used for preflight requests simply returns the server config
        """
        meta = frappe.cache.exists(f"drive_{fileID}")
        if meta is None:
            response.status_code = 404
            return
        response.headers.add("Tus-Extension", tus_extension)
        response.headers.add("Tus-Resumable", tus_version)
        response.headers.add("Tus-Version", tus_version)
        response.headers.add("Tus-Max-Size", str(max_size))
        response.headers.add("Content-Length", str(0))
        response.status_code = 204
        return

    if frappe.request.method == "DELETE":
        """
        wipe the file if it exists in the /uploads folder
        """
        return response


# background job to wipe file in /uploads if expiry is up
