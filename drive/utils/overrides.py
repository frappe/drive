import frappe


def common_filters(func):
    def decorator(user):
        user = user or frappe.session.user
        if user == "Administrator" or "Drive Admin" in frappe.get_roles():
            return ""
        return func(frappe.db.escape(user))

    return decorator


@common_filters
def filter_drive_permission(user):
    return f"""(`tabDrive Permission`.`owner` = {user} or `tabDrive Permission`.user = {user})"""


@common_filters
def filter_drive_team(user):
    return f"""(`tabDrive Team`.name in (select parent from `tabDrive Team Member` where user = {user}))"""


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


@common_filters
def filter_drive_settings(user):
    return f"(`tabDrive Settings`.`user` = {user})"


# Records that belong to one person, and the fields naming people who can see them.
# Only the person in the first field can create or change a record.
PERSONAL_RECORDS = {
    "Drive Favourite": ("user",),
    "Drive Entity Log": ("user",),
    "Drive Settings": ("user",),
    "Drive Notification": ("to_user", "from_user"),
}


def is_own_record(doc, ptype=None, user=None, debug=False):
    """Matches the list filters above for single records."""
    user = user or frappe.session.user
    if user == "Administrator" or "Drive Admin" in frappe.get_roles(user):
        return True
    fields = PERSONAL_RECORDS[doc.doctype]
    if ptype in (None, "read", "select"):
        return any(doc.get(field) == user for field in fields)
    person = fields[0]
    if doc.get(person) != user:
        return False
    # Changes are checked on the edited record, so the saved record must also be theirs.
    # Otherwise people could claim a record by putting their own name on it.
    return doc.is_new() or frappe.db.get_value(doc.doctype, doc.name, person) == user
