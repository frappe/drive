import frappe
from drive.api.permissions import get_user_access


def user_has_permission(doc, ptype, user):
    if doc.owner == user:
        return True
    access = get_user_access(doc, user)
    if ptype in access:
        return access[ptype]


def filter_drive_entity(user):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return f"""(`tabDrive Entity`.`owner` = {frappe.db.escape(user)})"""


def filter_drive_document(user):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return f"""(`tabDrive Document`.`owner` = {frappe.db.escape(user)})"""


def filter_drive_favourite(user):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return f"""(`tabDrive Favourite`.`user` = {frappe.db.escape(user)})"""


def filter_drive_recent(user):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return f"""(`tabDrive Entity Log`.`user` = {frappe.db.escape(user)})"""


def filter_drive_notif(user):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return """(`tabDrive Notification`.to_user = {user} or `tabDrive Notification`.from_user = {user})""".format(
        user=frappe.db.escape(user)
    )
