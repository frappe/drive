"""
Create framework `File` records from legacy `Drive File` rows.
"""

import frappe
from drive.utils import MIME_LIST_MAP, PRESENTATION_CONTENT_DOCTYPE, STATUS_ACTIVE, STATUS_TRASHED, WRITER_CONTENT_DOCTYPE
from drive.utils.files import get_s3_url

LEGACY_DOCTYPE = "Drive File"


def get_file_type(row):
    if row["is_group"]:
        return "Folder"
    if row["is_link"]:
        return "Link"
    try:
        return next(k for (k, v) in MIME_LIST_MAP.items() if row["mime_type"] in v)
    except StopIteration:
        return "Unknown"


def execute(files=None):
    if not frappe.db.table_exists(f"tab{LEGACY_DOCTYPE}"):
        return

    frappe.flags.mute_drive_activity_log = True
    try:
        root_files = files or frappe.get_all(LEGACY_DOCTYPE, filters={"parent_entity": ""}, pluck="name")

        is_remote = frappe.get_single("Drive Disk Settings").enabled
        failures = []
        for file_id in root_files:
            migrate_folder(file_id, is_remote, failures)

        if failures:
            print(f"Migration finished with {len(failures)} failure(s): {failures}")
    finally:
        frappe.flags.mute_drive_activity_log = False


def migrate_folder(folder_name, is_remote=False, failures=None):
    print(f"Migrating folder {folder_name}")
    folder = frappe.get_doc(LEGACY_DOCTYPE, folder_name)
    migrate_file(folder, is_remote, failures)

    for child_name in frappe.get_all(LEGACY_DOCTYPE, filters={"parent_entity": folder_name}, pluck="name"):
        child = frappe.get_doc(LEGACY_DOCTYPE, child_name)
        if child.is_group or child.doc:
            migrate_folder(child_name, is_remote, failures)
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
    if frappe.db.exists("File", {"name": file.name, "team": file.team}):
        return

    ff_file = frappe.get_doc(
        {
            "doctype": "File",
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
        ff_file.content_doctype = WRITER_CONTENT_DOCTYPE
        ff_file.content_docname = file.doc

    if file.mime_type == "frappe/slides":
        ff_file.content_doctype = PRESENTATION_CONTENT_DOCTYPE
        ff_file.content_docname = file.path

    if frappe.db.get_value(LEGACY_DOCTYPE, file.parent_entity, "doc"):
        ff_file.attached_to_doctype = "File"
        ff_file.attached_to_name = file.parent_entity

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
