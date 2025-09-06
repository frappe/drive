import frappe


def execute():
    for k in frappe.get_all("Drive File", fields=["name", "modified"]):
        frappe.db.set_value(
            "Drive File",
            k.name,
            "_modified",
            k.modified.strftime("%Y-%m-%d %H:%M:%S.%f"),
            update_modified=False,
        )
