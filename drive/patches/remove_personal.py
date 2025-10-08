import time
from pathlib import Path

import frappe


def execute():
    print(
        "This migration to a beta release might CORRUPT your data. Do NOT run this before taking a complete backup. You have two minutes left to cancel this deployment. "
    )
    # time.sleep(120)

    frappe.reload_doc("Drive", "doctype", "Drive Disk Settings")
    doc = frappe.get_single("Drive Disk Settings")
    doc.team_prefix = "team_name"
    doc.save()

    frappe.reload_doc("Drive", "doctype", "Drive Permission")
    # Change team shares
    for share in frappe.get_list("Drive Permission", filters={"user": "$TEAM"}, fields=["name", "entity"]):
        team = frappe.db.get_value("Drive File", share["entity"], "team")
        frappe.db.set_value("Drive Permission", share["name"], "user", team)
        frappe.db.set_value("Drive Permission", share["name"], "team", 1)

    if frappe.get_value("Drive Permission", {"user": "$TEAM"}, "name"):
        raise ValueError("Not all perms migrated!")

    # Insert personal team for every user if not exists
    frappe.reload_doc("Drive", "doctype", "Drive Team")
    MAP = {}
    for user in frappe.get_all("User", pluck="name"):
        if user == "Guest":
            continue
        frappe.session.user = user
        team = frappe.db.exists({"doctype": "Drive Team", "personal": 1, "owner": user})
        if not team:
            team = frappe.get_doc({"doctype": "Drive Team", "title": user, "personal": 1})
            team.insert()
            print(f"Created personal team {team.name} for user {user}")
            frappe.db.set_value("Drive Team", team.name, "owner", user)
            MAP[user] = team.name
        else:
            print(f"Using pre-existing team {team} for {user}")
            MAP[user] = team

    frappe.session.user = "Administrator"

    frappe.reload_doc("Drive", "doctype", "Drive File")
    # Move all is_private files to personal team
    for f in frappe.get_all(
        "Drive File",
        filters={"is_private": 1},
        fields=["name", "is_private", "owner", "parent_entity"],
    ):
        try:
            frappe.db.set_value("Drive File", f.name, "team", MAP[f.owner], update_modified=False)
            # For root elements, change parent folder
            if not frappe.db.get_value("Drive File", f.parent_entity, "parent_entity"):
                new_parent = frappe.db.get_value("Drive File", {"team": MAP[f.owner], "parent_entity": None}, "name")
                frappe.db.set_value("Drive File", f.name, "parent_entity", new_parent)
        except KeyError:
            print(f"There was an issue with the file {f} owned by {f.owner}")

    frappe.db.commit()
