# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.client import set_value

from drive.api.files import call_controller_method, create_folder, get_file_content, save_doc, stream_file_content
from drive.tests.utils import DriveTestCase, make_file, make_team, OTHER
from drive.utils.files import FileManager

OUTSIDE_PATH = "../../../../drive-outside.txt"


class TestStorageFields(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "note.md", "hello")
        self.manager = FileManager()

    def test_owner_cannot_change_storage_fields(self):
        other_team = make_team(OTHER)
        other_document = frappe.get_doc({"doctype": "Drive Document", "title": "x"}).insert(ignore_permissions=True)
        changes = (("path", OUTSIDE_PATH), ("team", other_team), ("document", other_document.name), ("mime_type", "frappe_doc"))
        for field, value in changes:
            with self.subTest(field=field), self.assertRaises(frappe.PermissionError):
                set_value("Drive File", self.file.name, field, value)
        doc = frappe.get_doc("Drive File", self.file.name)
        doc.path = OUTSIDE_PATH
        with self.assertRaises(frappe.PermissionError):
            doc.save()

    def test_files_cannot_be_created_outside_drive(self):
        doc = frappe.get_doc(
            {"doctype": "Drive File", "title": "x.txt", "team": self.team, "parent_entity": self.home, "path": OUTSIDE_PATH}
        )
        with self.assertRaises(frappe.PermissionError):
            doc.insert()

    def test_drive_can_still_rename_and_move(self):
        folder = create_folder(self.team, "Folder")
        frappe.local.form_dict = frappe._dict(entity_name=self.file.name, method="rename", new_title="renamed.md")
        call_controller_method()
        frappe.get_doc("Drive File", self.file.name).move(folder.name)
        path = frappe.db.get_value("Drive File", self.file.name, "path")
        self.assertEqual((self.manager.site_folder / path).read_text(), "hello")

    def test_names_with_slashes_are_refused(self):
        frappe.local.form_dict = frappe._dict(entity_name=self.file.name, method="rename", new_title="../renamed.md")
        with self.assertRaises(frappe.ValidationError):
            call_controller_method()

    def test_stored_paths_outside_storage_are_never_opened(self):
        # A path stored by an earlier version
        frappe.db.set_value("Drive File", self.file.name, "path", OUTSIDE_PATH)
        outside = self.manager.site_folder / OUTSIDE_PATH

        with self.assertRaises(frappe.PermissionError):
            save_doc(self.file.name, content="<p>changed</p>")
        self.assertFalse(outside.exists())

        with self.assertRaises(frappe.PermissionError):
            get_file_content(self.file.name)

        frappe.local.request = frappe._dict(headers={"Range": "bytes=0-"})
        frappe.db.set_value("Drive File", self.file.name, "mime_type", "video/mp4")
        with self.assertRaises(frappe.PermissionError):
            stream_file_content(self.file.name)

    def test_absolute_paths_are_refused(self):
        with self.assertRaises(frappe.PermissionError):
            self.manager.resolve("/etc/passwd")
