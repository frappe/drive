# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import io

import frappe
from frappe.tests import IntegrationTestCase
from werkzeug.datastructures import FileStorage

from drive.utils import create_drive_file, get_home_folder
from drive.utils.files import FileManager, storage_key

OWNER = "drive-owner@test.io"
OTHER = "drive-other@test.io"
THIRD = "drive-third@test.io"


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


def add_member(team, user, access_level=1):
    doc = frappe.get_doc("Drive Team", team)
    doc.append("users", {"user": user, "access_level": access_level})
    doc.save(ignore_permissions=True)


def make_file(team, file_name, content="", parent=None):
    """Create a Drive file with `content` on disk."""
    home = get_home_folder(team)
    manager = FileManager()
    drive_file = create_drive_file(
        team,
        file_name,
        parent or home["name"],
        "Text",
        lambda entity: "/" + str(manager.get_disk_path(entity, home)),
        "text/plain",
        len(content),
    )
    disk_path(drive_file.name).write_text(content)
    return drive_file


def disk_path(name):
    return FileManager().site_folder / storage_key(frappe.db.get_value("File", name, "file_url"))


def read_file(name):
    return disk_path(name).read_text()


def attach_upload(content=b"content", filename="report.txt", **form):
    frappe.local.form_dict = frappe._dict(form)
    frappe.local.request = frappe._dict(
        files={"file": FileStorage(stream=io.BytesIO(content), filename=filename)}
    )


class DriveTestCase(IntegrationTestCase):
    """Runs as OWNER, who owns a fresh team. Files are stored on disk in folders, not flat."""

    def setUp(self):
        frappe.db.set_single_value("Drive Disk Settings", {"enabled": 0, "flat": 0})
        for user in (OWNER, OTHER, THIRD):
            make_user(user)
        self.team = make_team(OWNER)
        self.home = get_home_folder(self.team)["name"]
        frappe.set_user(OWNER)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.local.form_dict = frappe._dict()
