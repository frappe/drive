from .files import get_file_content
import frappe


@frappe.whitelist(allow_guest=True)
def get_file(key):
    get_file_content(entity_name=key)
