# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from urllib.parse import quote

import frappe

from drive.tests.utils import OTHER, DriveTestCase, make_file
from drive.utils import get_home_folder


def new_site_file(**fields):
    return frappe.get_doc({"doctype": "File", "is_private": 1, **fields}).insert()


class TestSiteFiles(DriveTestCase):
    """Frappe's own File records, such as desk attachments, next to Drive's files on disk."""

    def test_site_files_cannot_point_into_team_folders(self):
        notes = make_file(self.team, "notes.txt", "hello")
        home = get_home_folder(self.team)["path"].rstrip("/")
        frappe.set_user(OTHER)
        paths = [notes.path, quote(notes.path), f"{home}/.thumbnails/{notes.name}.thumbnail", f"x/../{notes.path}"]
        for path in paths:
            with self.subTest(path=path), self.assertRaises(frappe.PermissionError):
                new_site_file(file_url=f"/private/files/{path}")

    def test_site_files_still_work(self):
        frappe.set_user(OTHER)
        first = new_site_file(file_name="site-notes.txt", content="hello")
        self.assertEqual(first.get_content(), "hello")
        second = new_site_file(file_url=first.file_url)
        self.assertEqual(second.get_content(), "hello")
        frappe.set_user("Administrator")
        todo = frappe.get_doc({"doctype": "ToDo", "description": "Read notes"}).insert()
        attachment = new_site_file(
            file_name="todo-notes.txt", content="hello", attached_to_doctype="ToDo", attached_to_name=todo.name
        )
        self.assertEqual(attachment.get_content(), "hello")
