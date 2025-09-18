import frappe


def presentation(doc, event):
    file = frappe.get_value("Drive File", {"path": doc.name}, "name")

    if file:
        if event == "on_update":
            frappe.get_doc("Drive File", file).rename(doc.title)
        if event == "on_trash":
            print("gone, boom boom")
            frappe.get_doc("Drive File", file).permanent_delete()
