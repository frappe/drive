import frappe
from drive.api.permissions import user_group_entity_access


def user_has_permission(doc, ptype, user):
    if not user:
        user = frappe.session.user

    if doc.owner == user:
        return

    if user != "Guest":
        user_access = frappe.db.get_value(
            "Drive DocShare",
            {
                "share_doctype": "Drive Entity",
                "share_name": doc.name,
                "user_doctype": "User",
                "user_name": frappe.session.user,
            },
            ["read", "write"],
            as_dict=1,
        )
        if user_access:
            if ptype == "share" and user_access["read"]:
                return
            if ptype == "write" and user_access["write"]:
                return
            if ptype == "read" and user_access["read"]:
                return
        group_access = user_group_entity_access(doc.name)
        if group_access:
            if ptype == "share" and group_access["read"]:
                return
            if ptype == "write" and group_access["write"]:
                return
            if ptype == "read" and group_access["read"]:
                return
        general_access = frappe.db.get_value(
            "Drive DocShare",
            {"share_name": doc.name, "everyone": 1},
            ["read", "write"],
            as_dict=1,
        )
        if general_access:
            if ptype == "write" and general_access["write"]:
                return
            if ptype == "read" and general_access["read"]:
                return
        public_access = frappe.db.get_value(
            "Drive DocShare",
            {"share_name": doc.name, "public": 1},
            ["read", "write"],
            as_dict=1,
        )
        if public_access:
            if ptype == "write" and public_access["write"]:
                return
            if ptype == "read" and public_access["read"]:
                return

        return False
    public_access = frappe.db.get_value(
        "Drive DocShare",
        {"share_name": doc.name, "public": 1},
        ["read", "write"],
        as_dict=1,
    )
    if public_access:
        if ptype == "write" and public_access["write"]:
            return
        if ptype == "read" and public_access["read"]:
            return
