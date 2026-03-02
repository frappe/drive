import frappe


def execute():
    for user in frappe.get_all("User", fields=["name", "enabled"]):
        if user.enabled:
            user_doc = frappe.get_doc("User", user.name)
            user_doc.add_roles("Drive User")
            user_doc.save()
