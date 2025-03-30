import frappe


def scan(folder):
    folder = frappe.get_doc("Drive File", folder)
    child_folders = frappe.get_list(
        "Drive File", {"parent_entity": folder.name, "is_group": 1}, pluck="name"
    )
    for child in child_folders:
        scan(child)
    sizes = frappe.get_list(
        "Drive File", {"parent_entity": folder.name, "is_active": 1}, pluck="file_size"
    )
    frappe.db.set_value("Drive File", folder.name, "file_size", sum(sizes), update_modified=False)


def execute():
    roots = frappe.get_list("Drive File", {"parent_entity": ""}, pluck="name")
    for root in roots:
        scan(root)
