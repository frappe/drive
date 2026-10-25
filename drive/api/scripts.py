import frappe

from drive.utils import STATUS_TRASHED, STATUS_REMOVED
from drive.api.files import delete_entities
from datetime import date, timedelta


def auto_delete_from_trash():
    days_before = (date.today() - timedelta(days=30)).isoformat()
    result = frappe.db.get_all(
        "File",
        filters={"status": STATUS_TRASHED, "file_modified": ["<", days_before]},
        fields=["name"],
    )
    delete_entities(result)


def clear_deleted_files():
    days_before = (date.today() - timedelta(days=30)).isoformat()
    result = frappe.db.get_all(
        "File",
        filters={"status": STATUS_REMOVED, "modified": ["<", days_before]},
        fields=["name"],
    )
    for entity in result:
        doc = frappe.get_doc("File", entity, ignore_permissions=True)
        doc.delete()
