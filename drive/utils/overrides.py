import frappe


def common_filters(func):
    def decorator(user):
        user = user or frappe.session.user
        if user == "Administrator" or "Drive Admin" in frappe.get_roles():
            return ""
        return func(frappe.db.escape(user))

    return decorator


@common_filters
def filter_drive_file(user):
    return f"""(`tabDrive File`.`owner` = {user})"""


@common_filters
def filter_drive_permission(user):
    return f"""(`tabDrive Permission`.`owner` = {user} or `tabDrive Permission`.user = {user})"""


@common_filters
def filter_drive_team(user):
    return f"""(`tabDrive Team`.name in (
        select parent from `tabDrive Team Member` where parenttype = 'Drive Team' and user = {user}
    ))"""


@common_filters
def filter_drive_document(user):
    return f"""(`tabDrive Document`.`owner` = {user})"""


@common_filters
def filter_drive_comment(user):
    return f"""(`tabDrive Comment`.`owner` = {user})"""


@common_filters
def filter_drive_favourite(user):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    return f"""(`tabDrive Favourite`.`user` = {user})"""


@common_filters
def filter_drive_recent(user):
    return f"""(`tabDrive Entity Log`.`user` = {user})"""


@common_filters
def filter_drive_notif(user):
    return f"(`tabDrive Notification`.to_user = {user} or `tabDrive Notification`.from_user = {user})"
