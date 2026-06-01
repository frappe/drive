import frappe
from frappe import _
from drive.api.files import get_file_content, get_s3_url


@frappe.whitelist(allow_guest=True)
def fetch(path: str):
    name = frappe.db.get_value("File", {"file_url": get_s3_url(path)})
    if not name:
        frappe.throw(_("Not found"), frappe.DoesNotExistError)
    try:
        return get_file_content(name)
    except (frappe.PermissionError, frappe.DoesNotExistError):
        frappe.throw(_("Not found"), frappe.DoesNotExistError)
