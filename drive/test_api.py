# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import frappe


def whitelist(fn):
    if not frappe.conf.enable_ui_tests:
        frappe.throw("Cannot run UI tests. Set 'enable_ui_tests' in site_config.json to continue.")

    whitelisted = frappe.whitelist(allow_guest=True)(fn)
    return whitelisted


@whitelist
def clear_data():
    doctypes = frappe.get_all("DocType", filters={"module": "Drive", "issingle": 0}, pluck="name")
    for doctype in doctypes:
        frappe.db.delete(doctype)

    frappe.set_user("Administrator")
    admin = frappe.get_doc("User", "Administrator")
    admin.add_roles("Drive Admin")

    if not frappe.db.exists("User", "four@test.io"):
        user = frappe.get_doc(
            doctype="User",
            email="four@test.io",
            first_name="Four",
            last_name="McTest",
            send_welcome_email=0,
        )
        user.insert()

    keep_users = ["Administrator", "Guest", "four@test.io"]
    for user in frappe.get_all("User", filters={"name": ["not in", keep_users]}):
        frappe.delete_doc("User", user.name)
