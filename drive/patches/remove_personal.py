import time
from pathlib import Path

import frappe


def execute():
    print(
        "This migration to a beta release might CORRUPT your data. Do NOT run this before taking a complete backup. You have two minutes left to cancel this deployment. "
    )
    time.sleep(120)

    # Insert personal team for every user if not exists
    MAP = {}
    for user in frappe.get_all("Drive Team", pluck="name"):
        team = frappe.get_doc({"doctype": "Drive Team", "personal": 1})
        team.insert()
        print(f"Created personal team {team.name} for user {user}")
        MAP[user] = team.name
        frappe.db.set_value("Drive Team", team.name, "owner", user)
    frappe.db.commit()

    frappe.reload_doc("Drive", "doctype", "Drive File")

    # Move all is_private files to personal team
    for f in frappe.get_all(
        "Drive File", filters={"is_private": 1}, fields=["name", "is_private"]
    ):
        frappe.db.set_value("Drive File", f.name, "team", MAP.get(f.owner))

    frappe.db.commit()
