import frappe


def user_has_permission(doc, ptype, user):
    if not user:
        user = frappe.session.user

    if doc.owner == user:
        return

    if user != "Guest":
        user_access = frappe.db.get_value(
            "DocShare",
            {"share_name": doc.name, "user": frappe.session.user},
            ["read", "write", "share"],
            as_dict=1,
        )
        if user_access:
            if ptype == "write" and user_access["write"]:
                return
            if ptype == "read" and user_access["read"]:
                return
        return False

    public_access = frappe.db.get_value(
        "DocShare",
        {"share_name": doc.name, "everyone": 1},
        ["read", "write"],
        as_dict=1,
    )
    if public_access:
        if ptype == "write" and public_access["write"]:
            return
        if ptype == "read" and public_access["read"]:
            return
