import frappe
from frappe.utils import get_fullname


def execute():
    all_shares = frappe.db.get_list(
        "Drive DocShare",
        fields=[
            "share_name",
            "user_doctype",
            "user_name",
            "creation",
            "everyone",
            "public",
            "read",
            "write",
            "owner",
        ],
        filters=[
            ["protected", "=", False],
        ],
    )
    for share in all_shares:
        log = create_activity_log(share)
        log.save()
        update_activity_log(log, share)


def create_activity_log(share):
    log = frappe.new_doc("Drive Entity Activity Log")
    log.entity = share.share_name
    log.action_type = "share_add"
    log.meta_value = 2 if share.write else 1
    log.owner = share.owner
    log.creation = share.creation
    return log


def update_activity_log(log, share):
    title = frappe.db.get_value("Drive File", share.share_name, ["title"])
    owner_fullname = get_fullname(share.owner)
    if share.everyone:
        log.document_field = "everyone"
        message = f"{owner_fullname} shared {title} with everyone"
        log.old_value = False
        log.new_value = True
    elif share.public:
        log.document_field = "public"
        message = f"{owner_fullname} shared {title} with publicly"
        log.old_value = False
        log.new_value = True
    elif share.user_doctype == "User Group":
        log.document_field = "User Group"
        message = f"{owner_fullname} shared {title} with {share.user_name}"
        log.old_value = None
        log.new_value = share.user_name
    else:
        log.document_field = "User"
        message = f"{owner_fullname} shared {title} with {share.user_name}"
        log.old_value = None
        log.new_value = share.user_name
    log.save()
    frappe.db.set_value("Drive Entity Activity Log", log.name, "message", message)
    frappe.db.set_value("Drive Entity Activity Log", log.name, "owner", share.owner)
    frappe.db.set_value("Drive Entity Activity Log", log.name, "creation", share.creation)
