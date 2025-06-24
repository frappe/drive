import frappe


def execute():
    frappe.reload_doc("Drive", "doctype", "Drive Team Member")
    for id in frappe.get_all("Drive Team Member"):
        member = frappe.get_doc("Drive Team Member", id)
        member.access_level = 2 if member.is_admin else 1
        member.save()
