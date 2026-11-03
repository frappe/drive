# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from drive.utils import create_drive_file, get_home_folder
from drive.utils.files import FileManager

OWNER = "drive-owner@test.io"
OTHER = "drive-other@test.io"


def make_user(email):
    if not frappe.db.exists("User", email):
        frappe.get_doc(
            doctype="User", email=email, first_name=email.split("@")[0], send_welcome_email=0
        ).insert(ignore_permissions=True)
    return email


def make_team(owner):
    """Create a team owned by `owner`. Titles are unique because team folders on disk outlive the test rollback."""
    current_user = frappe.session.user
    frappe.set_user(owner)
    team = frappe.get_doc({"doctype": "Drive Team", "title": f"Test {frappe.generate_hash(length=8)}"})
    team.insert(ignore_permissions=True)
    frappe.set_user(current_user)
    return team.name


def make_file(team, title, content="", parent=None):
    """Create a Drive File with `content` on disk."""
    home = get_home_folder(team)
    manager = FileManager()
    drive_file = create_drive_file(
        team,
        title,
        parent or home["name"],
        "text/plain",
        lambda entity: manager.get_disk_path(entity, home),
        file_size=len(content),
    )
    (manager.site_folder / drive_file.path).write_text(content)
    return drive_file


def read_file(name):
    path = frappe.db.get_value("Drive File", name, "path")
    return (FileManager().site_folder / path).read_text()


class DriveTestCase(IntegrationTestCase):
    """Runs as OWNER, who owns a fresh team. Files are stored on disk in folders, not flat."""

    def setUp(self):
        frappe.db.set_single_value("Drive Disk Settings", {"enabled": 0, "flat": 0})
        make_user(OWNER)
        make_user(OTHER)
        self.team = make_team(OWNER)
        self.home = get_home_folder(self.team)["name"]
        frappe.set_user(OWNER)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.local.form_dict = frappe._dict()
