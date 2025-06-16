import frappe


def execute():
    for user in frappe.db.get_list("User", pluck="name"):
        teams = frappe.get_all(
            "Drive Team Member",
            pluck="parent",
            filters=[
                ["parenttype", "=", "Drive Team"],
                ["user", "=", user],
            ],
        )
        if teams:
            if not frappe.db.exists("Drive Settings", {"user": user}):
                frappe.get_doc(
                    {
                        "doctype": "Drive Settings",
                        "user": user,
                        "single_click": 1,
                        "default_team": teams[0],
                    }
                ).insert()
