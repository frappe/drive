"""
Create `File` records of all existing `Drive File`s
"""

import frappe
from drive.utils import MIME_LIST_MAP, STATUS_ACTIVE, STATUS_TRASHED
from drive.utils.files import get_s3_url


def get_file_type(r):
    if r["is_group"]:
        return "Folder"
    if r["is_link"]:
        return "Link"
    try:
        return next(k for (k, v) in MIME_LIST_MAP.items() if r["mime_type"] in v)
    except StopIteration:
        return "Unknown"


def execute(files=None):
    root_files = files or frappe.get_all("Drive File", filters={"parent_entity": ""}, pluck="name")

    is_remote = frappe.get_single("Drive Disk Settings").enabled
    failures = []
    for file_id in root_files:
        folder = frappe.get_doc("Drive File", file_id)
        migrate_folder(folder, is_remote, failures)

    if failures:
        print(f"Migration finished with {len(failures)} failure(s): {failures}")


def migrate_folder(folder, is_remote=False, failures=None):
    print(f"Migrating folder {folder}")
    migrate_file(folder, is_remote, failures)

    for child in folder.get_children():
        if child.is_group or child.doc:
            migrate_folder(child, is_remote, failures)
        else:
            migrate_file(child, is_remote, failures)


def get_link(file, is_remote=False):
    if file.mime_type == "frappe/slides" or not file.path:
        return ""
    elif file.is_link:
        return file.path
    elif is_remote:
        return get_s3_url(file.path)
        
    return "/private/files/" + file.path


def migrate_file(file, is_remote=False, failures=None):
    if frappe.db.exists("File", {"is_drive_file": 1, "name": file.name}):
        return

    ff_file = frappe.get_doc(
        {
            "doctype": "File",
            "is_drive_file": 1,
            "_name": file.name,
            "file_name": file.title,
            "team": file.team,
            "file_url": get_link(file, is_remote),
            "folder": file.parent_entity,
            "is_folder": file.is_group,
            "file_size": file.file_size,
            "file_modified": file._modified,
            "status": STATUS_ACTIVE if file.is_active else STATUS_TRASHED,
            "mime_type": file.mime_type,
            "is_private": 1,
        }
    )

    if file.doc:
        ff_file.content_doctype = "Writer Document"
        ff_file.content_docname = file.doc

    if file.mime_type == "frappe/slides":
        ff_file.content_doctype = "Presentation"
        ff_file.content_docname = file.path

    # Attachment
    if frappe.db.get_value("Drive File", file.parent_entity, "doc"):
        ff_file.attached_to_doctype = "File"
        ff_file.attached_to_name = file.parent_entity

    # Calculate file type
    ff_file.file_type = get_file_type(file.as_dict())

    try:
        ff_file.insert()
        frappe.db.set_value("File", ff_file.name, "creation", file.creation, update_modified=False)
        frappe.db.set_value("File", ff_file.name, "owner", file.owner, update_modified=False)
        frappe.db.set_value("File", ff_file.name, "modified", file.modified, update_modified=False)
    except Exception as e:
        print(f"Error migrating file {file.name}: {e}")
        if failures is not None:
            failures.append(file.name)
