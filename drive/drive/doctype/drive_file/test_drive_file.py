# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

# import frappe
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from drive.drive.doctype.drive_file.drive_file import DriveFile


def _insert_fixture(doc):
    doc.flags.allow_storage_change = True
    return doc.insert(ignore_permissions=True)


def _fake_drive_file(title, parent_entity, path=None):
    obj = DriveFile.__new__(DriveFile)
    obj.name = "test-doc"
    obj.title = title
    obj.parent_entity = parent_entity
    obj.path = path
    obj.is_active = 1
    obj.is_link = 0
    obj.mime_type = None
    return obj


class TestDriveFile(FrappeTestCase):
    """
    Unit tests for DriveFile.
    Use this class for testing individual functions and methods.
    """

    def setUp(self):
        # Root folder (home) whose *path* differs from its *title* -- the exact
        # condition that caused uploads to 500.
        self.team = frappe.get_doc(
            {
                "doctype": "Drive Team",
                "title": "Test Team",
            }
        ).insert(ignore_permissions=True)
        self.home = _insert_fixture(frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": "Drive - " + self.team.name,
                "path": "rootpath@example.com",
                "parent_entity": None,
                "is_group": 1,
                "team": self.team.name,
                "is_active": 1,
            }
        ))
        self.folder = _insert_fixture(frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": "Folder A",
                "path": "rootpath@example.com/Folder A",
                "parent_entity": self.home.name,
                "is_group": 1,
                "team": self.team.name,
                "is_active": 1,
            }
        ))

    def tearDown(self):
        frappe.delete_doc("Drive File", self.folder.name, force=True, ignore_permissions=True)
        frappe.delete_doc("Drive File", self.home.name, force=True, ignore_permissions=True)
        frappe.delete_doc("Drive Team", self.team.name, force=True, ignore_permissions=True)

    def test_canonical_path_uses_root_path_not_title(self):
        doc = _fake_drive_file("file.txt", self.folder.name)
        expected = str(Path("rootpath@example.com") / "Folder A" / "file.txt")
        self.assertEqual(doc.get_canonical_path(), expected)

    def test_repair_does_not_rewrite_correct_path(self):
        correct = str(Path("rootpath@example.com") / "Folder A" / "file.txt")
        doc = _fake_drive_file("file.txt", self.folder.name, path=correct)
        doc.repair_path_drift()
        self.assertEqual(doc.path, correct)

    def test_repair_skips_empty_path(self):
        doc = _fake_drive_file("file.txt", self.folder.name, path=None)
        doc.repair_path_drift()
        self.assertIsNone(doc.path)