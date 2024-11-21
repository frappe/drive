import frappe
import os
from pathlib import Path
import hashlib
from drive.locks.distributed_lock import DistributedLock
import json
from frappe.rate_limiter import rate_limit
from frappe.utils import now, split_emails, validate_email_address


@frappe.whitelist()
def get_users_with_drive_user_role_and_groups(txt=""):
    role_filters = ["Drive User", "Drive Admin", "Drive Guest"]
    try:
        drive_groups = frappe.get_all("User Group")
        drive_users = frappe.get_all(
            doctype="User",
            filters=[
                ["Has Role", "role", "in", role_filters],
                ["full_name", "not like", "Administrator"],
                ["full_name", "not like", "Guest"],
            ],
            fields=[
                "email",
                "full_name",
                "user_image",
            ],
        )
        return drive_users + drive_groups

    except Exception as e:
        frappe.log_error("Error in fetching Drive Users: {0}".format(e))
        return {
            "status": "error",
            "message": "An error occurred while fetching Drive Users",
        }


@frappe.whitelist()
def get_users_with_drive_user_role(txt="", get_roles=False):
    role_filters = ["Drive User", "Drive Admin", "Drive Guest"]
    try:
        drive_users = frappe.get_all(
            doctype="User",
            order_by="full_name",
            filters=[
                ["Has Role", "role", "in", role_filters],
                ["full_name", "not like", "Administrator"],
                ["full_name", "not like", "Guest"],
                ["full_name", "like", f"%{txt}%"],
            ],
            fields=[
                "email",
                "full_name",
                "user_image",
            ],
        )
        if get_roles == "true":
            for user in drive_users:
                if frappe.db.exists("Has Role", {"parent": user.email, "role": "Drive Admin"}):
                    user["role"] = "Admin"
                elif frappe.db.exists("Has Role", {"parent": user.email, "role": "Drive User"}):
                    user["role"] = "User"
                elif frappe.db.exists("Has Role", {"parent": user.email, "role": "Drive Guest"}):
                    user["role"] = "Guest"

        return drive_users

    except Exception as e:
        frappe.log_error("Error in fetching Drive Users: {0}".format(e))
        return {
            "status": "error",
            "message": "An error occurred while fetching Drive Users",
        }


@frappe.whitelist()
def add_drive_user_role(user_id, user_role):
    allowed_roles = {"Drive User", "Drive Admin", "Drive Guest"}

    if user_role not in allowed_roles:
        frappe.throw("Invalid Role")

    if not frappe.has_permission(
        doctype="User",
        doc=user_id,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to edit roles")

    drive_user = frappe.db.exists("User", {"name": ("like", f"%{user_id}%")})

    if not drive_user:
        frappe.throw("User does not exist")

    usr = frappe.get_doc("User", user_id)

    for role in allowed_roles:
        user_role_exists = frappe.db.exists("Has Role", {"parent": user_id, "role": role})
        if user_role_exists is not None:
            # just wipe all for now to prevent multiple drive roles
            usr.remove_roles(role)
    usr.add_roles(user_role)
    return


@frappe.whitelist()
def remove_drive_user_role(user_id, user_role):
    allowed_roles = {"Drive User", "Drive Admin", "Drive Guest"}

    if user_role not in allowed_roles:
        frappe.throw("Invalid Role")

    if not frappe.has_permission(
        doctype="User",
        doc=user_id,
        ptype="write",
        user=frappe.session.user,
    ):
        raise frappe.PermissionError("You do not have permission to edit roles")

    drive_user = frappe.db.exists("User", {"name": ("like", f"%{user_id}%")})

    if not drive_user:
        frappe.throw("User does not exist")

    usr = frappe.get_doc("User", user_id)
    for role in allowed_roles:
        user_role_exists = frappe.db.exists("Has Role", {"parent": user_id, "role": role})
        if user_role_exists is not None:
            usr.remove_roles(role)
    return


def has_read_write_access_to_doctype(user_id, doctype_name):
    """
    Check if a user has both read and write access to a DocType.

    Args:
        user_id (str): The name of the user to check.
        doctype_name (str): The name of the DocType to check access for.

    Returns:
        bool: True if the user has both read and write access to the DocType, False otherwise.
    """
    try:
        if frappe.has_permission(doctype_name, user=user_id, ptype="read"):
            if frappe.has_permission(doctype_name, user=user_id, ptype="write"):
                return True
    except frappe.PermissionError:
        pass

    return False


def mark_as_viewed(entity):
    if frappe.session.user == "Guest":
        return
    if not frappe.has_permission(
        doctype="Drive Entity Log", ptype="write", user=frappe.session.user
    ):
        return
    if entity.is_group:
        return
    entity_name = entity.name
    entity_log = frappe.db.get_value(
        "Drive Entity Log", {"entity_name": entity_name, "user": frappe.session.user}
    )
    if entity_log:
        frappe.db.set_value(
            "Drive Entity Log", entity_log, "last_interaction", now(), update_modified=False
        )
        return
    doc = frappe.new_doc("Drive Entity Log")
    doc.entity_name = entity_name
    doc.user = frappe.session.user
    doc.last_interaction = now()
    doc.insert()
    return doc


@frappe.whitelist()
def drive_user_level():
    user = frappe.session.user
    if user == "Administrator":
        return "Drive Admin"

    if user != "Guest":
        if frappe.db.exists("Has Role", {"parent": user, "role": "Drive Admin"}):
            return "Drive Admin"
        if frappe.db.exists("Has Role", {"parent": user, "role": "Drive User"}):
            return "Drive User"
        if frappe.db.exists("Has Role", {"parent": user, "role": "Drive Guest"}):
            return "Drive Guest"
        return "Guest"
    raise frappe.PermissionError("Unauthorized", frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def accept_invitation(key):
    if not key:
        frappe.throw("Invalid or expired key")

    invitation_name = frappe.db.exists("Drive User Invitation", {"key": key})
    if not invitation_name:
        frappe.throw("Invalid or expired key")

    invitation = frappe.get_doc("Drive User Invitation", invitation_name)
    invitation.accept()
    invitation.reload()

    if invitation.status == "Accepted":
        add_drive_user_role(invitation.email)
        frappe.local.login_manager.login_as(invitation.email)
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/drive"


@frappe.whitelist()
def invite_users(emails, role="Drive User"):
    if not emails:
        return

    email_string = validate_email_address(emails, throw=False)
    email_list = split_emails(email_string)
    if not email_list:
        return

    existing_invites = frappe.db.get_list(
        "Drive User Invitation",
        filters={
            "email": ["in", email_list],
            "status": ["in", ["Pending", "Accepted"]],
        },
        pluck="email",
    )

    new_invites = list(set(email_list) - set(existing_invites))
    for email in new_invites:
        invite = frappe.new_doc("Drive User Invitation")
        invite.email = email
        invite.role = role
        invite.insert(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
@rate_limit(key="reference_name", limit=10, seconds=60 * 60)
def add_comment(reference_name: str, content: str, comment_email: str, comment_by: str) -> "Comment":
    """Allow logged user with permission to read document to add a comment"""
    entity = frappe.get_doc("Drive Entity", reference_name)
    if not entity.allow_comments:
        return
    comment = frappe.new_doc("Comment")
    comment.update(
        {
            "comment_type": "Comment",
            "reference_doctype": "Drive Entity",
            "reference_name": entity,
            "comment_email": comment_email,
            "comment_by": comment_by,
            "content": content,
        }
    )
    comment.insert(ignore_permissions=True)
    return comment