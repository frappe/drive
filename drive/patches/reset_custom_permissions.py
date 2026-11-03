import frappe
from frappe.permissions import reset_perms

DOCTYPES = ("Drive Permission", "Drive Team", "Drive User Invitation")


def execute():
    """Drop customised permissions so the ones defined in each DocType apply."""
    for doctype in DOCTYPES:
        reset_perms(doctype)
        frappe.clear_cache(doctype=doctype)
