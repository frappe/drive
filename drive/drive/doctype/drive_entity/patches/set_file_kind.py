import frappe
from drive.api.format import mime_to_human


def execute():
    all_entities = frappe.db.get_all(
        "Drive Entity", fields=["name", "mime_type", "file_kind", "is_group"]
    )
    for i in all_entities:
        eval = mime_to_human(i.mime_type, i.is_group)
        frappe.db.set_value("Drive Entity", i.name, "file_kind", eval, update_modified=False)
