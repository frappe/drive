import frappe
import os
from pathlib import Path
import hashlib
from drive.locks.distributed_lock import DistributedLock
import json


@frappe.whitelist()
def get_users_with_drive_user_role(txt=""):
    try:
        drive_users = frappe.get_all(
            doctype="User",
            filters=[
                ["Has Role", "role", "=", "Drive User"],
                ["full_name", "like", f"%{txt}%"],
            ],
            fields=[
                "email",
                "full_name",
            ],
        )
        if len(drive_users) == 0:
            empty_results = {"results": drive_users}
            return empty_results
        renamed_users = []
        for user in drive_users:
            renamed_user = {
                "value": user.email,
                "description": user.full_name,
            }
            renamed_users.append(renamed_user)
            custom_response = {"results": renamed_users}
        return custom_response
    except Exception as e:
        frappe.log_error("Error in fetching Drive Users: {0}".format(e))
        return {
            "status": "error",
            "message": "An error occurred while fetching Drive Users",
        }


@frappe.whitelist()
def get_all_users_on_site():
    try:
        has_rw_access = has_read_write_access_to_doctype(frappe.session.user, "User")
        if not has_rw_access:
            return {
                "status": "error",
                "message": "You do not have permission to access this resource",
            }

        site_users = frappe.get_all(
            doctype="User",
            fields=[
                "username",
                "email",
                "full_name",
            ],
        )

        return site_users

    except Exception as e:
        frappe.log_error("Error in fetching Drive Users: {0}".format(e))
        return {
            "status": "error",
            "message": "An error occurred while fetching Drive Users",
        }


@frappe.whitelist()
def add_drive_user_role(user_id):
    has_rw_access = has_read_write_access_to_doctype(frappe.session.user, "User")

    if not has_rw_access:
        return {
            "status": "error",
            "message": "You do not have permission to access this resource",
        }

    drive_user = frappe.db.exists("User", {"name": ("like", f"%{user_id}%")})

    if not drive_user:
        return {"status": "error", "message": "User with given email does not exist"}

    user_role_exists = frappe.db.exists(
        "Has Role", {"parent": user_id, "role": "Drive User"}
    )

    if user_role_exists is not None:
        return {
            "status": "error",
            "message": "User already has the said  Role permissions ",
        }

    usr = frappe.get_doc("User", user_id)

    usr.add_roles("Drive User")

    return {"status": "sucess", "message": "Drive User role has been sucessfully added"}


@frappe.whitelist()
def remove_drive_user_role(user_id):
    has_rw_access = has_read_write_access_to_doctype(frappe.session.user, "User")

    if not has_rw_access:
        return {
            "status": "error",
            "message": "You do not have permission to access this resource",
        }

    drive_user = frappe.db.exists("User", {"name": ("like", f"%{user_id}%")})

    if not drive_user:
        return {"status": "error", "message": "User with given email does not exist"}

    user_role_exists = frappe.db.exists(
        "Has Role", {"parent": user_id, "role": "Drive User"}
    )

    if user_role_exists is None:
        return {
            "status": "error",
            "message": "User does not have Drive User as a role applied ",
        }

    usr = frappe.get_doc("User", user_id)

    usr.remove_roles("Drive User")

    return {
        "status": "sucess",
        "message": "Drive User role has been sucessfully removed",
    }


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
