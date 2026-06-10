"""
Create framework `File` records from legacy `Drive File` rows.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from drive.utils import MIME_LIST_MAP, PRESENTATION_CONTENT_DOCTYPE, STATUS_ACTIVE, STATUS_TRASHED, WRITER_CONTENT_DOCTYPE
from drive.utils.files import get_s3_url

LEGACY_DOCTYPE = "Drive File"


def ensure_custom_fields():
    """Drive's File columns ship as fixtures, which sync after pre_model_sync patches.
    Create them up front so the migration below can write to them."""
    with open(frappe.get_app_path("drive", "fixtures", "custom_field.json")) as f:
        fields = json.load(f)

    custom_fields = {}
    for df in fields:
        custom_fields.setdefault(df["dt"], []).append(df)

    create_custom_fields(custom_fields, ignore_validate=True)


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
    if not frappe.db.table_exists(LEGACY_DOCTYPE):
        return

    ensure_custom_fields()

    frappe.flags.mute_drive_activity_log = True
    try:
        root_files = files or frappe.get_all(LEGACY_DOCTYPE, filters={"parent_entity": ["is", "not set"]}, pluck="name")

        is_remote = frappe.get_single("Drive Disk Settings").enabled
        failures = []
        for file_id in root_files:
            migrate_folder(file_id, is_remote, failures)

        if failures:
            print(f"Migration finished with {len(failures)} failure(s): {failures}")
    finally:
        frappe.flags.mute_drive_activity_log = False


def get_legacy(name):
    # The Drive File doctype is deleted by the time this runs, so its controller
    # can't be imported; read rows as plain dicts (get_all needs only the meta).
    return frappe.get_all(LEGACY_DOCTYPE, filters={"name": name}, fields=["*"])[0]


def migrate_folder(folder_name, is_remote=False, failures=None):
    print(f"Migrating folder {folder_name}")
    migrate_file(get_legacy(folder_name), is_remote, failures)

    for child in frappe.get_all(LEGACY_DOCTYPE, filters={"parent_entity": folder_name}, fields=["*"]):
        if child.is_group or child.doc:
            migrate_folder(child.name, is_remote, failures)
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
    # File name is the global primary key; dedup on it alone so re-runs skip
    # rows from an earlier (partial) migration instead of colliding on insert.
    if frappe.db.exists("File", file.name):
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

    if file.doc and frappe.db.exists(WRITER_CONTENT_DOCTYPE, file.doc):
        ff_file.content_doctype = WRITER_CONTENT_DOCTYPE
        ff_file.content_docname = file.doc

    if file.mime_type == "frappe/slides" and frappe.db.exists(PRESENTATION_CONTENT_DOCTYPE, file.path):
        ff_file.content_doctype = PRESENTATION_CONTENT_DOCTYPE
        ff_file.content_docname = file.path

    if frappe.db.get_value(LEGACY_DOCTYPE, file.parent_entity, "doc"):
        ff_file.attached_to_doctype = "File"
        ff_file.attached_to_name = file.parent_entity

    ff_file.file_type = get_file_type(file)

    try:
        ff_file.insert()
        frappe.db.set_value("File", ff_file.name, "creation", file.creation, update_modified=False)
        frappe.db.set_value("File", ff_file.name, "owner", file.owner, update_modified=False)
        frappe.db.set_value("File", ff_file.name, "modified", file.modified, update_modified=False)
    except Exception as e:
        print(f"Error migrating file {file.name}: {e}")
        if failures is not None:
            failures.append(file.name)
