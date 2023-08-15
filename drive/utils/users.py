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
        if not frappe.session.user == "Administrator":
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