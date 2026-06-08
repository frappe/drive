import frappe

from drive.utils import PRESENTATION_CONTENT_DOCTYPE


def presentation(doc, event):
    file = frappe.db.get_value(
        "File",
        {"content_docname": doc.name, "content_doctype": PRESENTATION_CONTENT_DOCTYPE},
        "name",
    )

    if file:
        drive_file = frappe.get_doc("File", file)
        if event == "on_update":
            drive_file.rename(doc.file_name)
        if event == "on_trash":
            drive_file.permanent_delete()
