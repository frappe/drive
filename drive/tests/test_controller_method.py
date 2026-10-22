# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.handler import run_doc_method

from drive.api.files import call_controller_method, create_folder
from drive.tests.utils import OTHER, OWNER, DriveTestCase


def call(entity_name, method, **kwargs):
    frappe.local.form_dict = frappe._dict(cmd="x", entity_name=entity_name, method=method, **kwargs)
    return call_controller_method()


class TestCallControllerMethod(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.folder = create_folder(self.team, "Private folder")

    def title(self):
        return frappe.db.get_value("Drive File", self.folder.name, "title")

    def test_methods_outside_the_allowlist_are_refused(self):
        for method in ("db_set", "save", "delete", "move", "permanent_delete", "change_color", "recursive_path_move"):
            with self.subTest(method=method), self.assertRaises(frappe.PermissionError):
                call(self.folder.name, method, fieldname="path", value="other/path")

    def test_owner_can_rename(self):
        call(self.folder.name, "rename", new_title="Renamed by owner")
        self.assertEqual(self.title(), "Renamed by owner")

    def test_user_without_access_cannot_rename_share_or_unshare(self):
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            call(self.folder.name, "rename", new_title="Renamed by other")
        with self.assertRaises(frappe.PermissionError):
            call(self.folder.name, "share", user=OTHER, read=1, write=1)
        with self.assertRaises(frappe.PermissionError):
            call(self.folder.name, "unshare", user="$GENERAL")
        self.assertEqual(self.title(), "Private folder")
        self.assertFalse(frappe.db.exists("Drive Permission", {"entity": self.folder.name, "user": OTHER}))

    def test_reader_cannot_rename_but_can_leave(self):
        call(self.folder.name, "share", user=OTHER, read=1)
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            call(self.folder.name, "rename", new_title="Renamed by reader")
        call(self.folder.name, "unshare", user=OTHER)
        self.assertFalse(frappe.db.exists("Drive Permission", {"entity": self.folder.name, "user": OTHER}))

    def test_sharer_cannot_give_more_access_than_they_have(self):
        call(self.folder.name, "share", user=OTHER, read=1, share=1)
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            call(self.folder.name, "share", user=OTHER, read=1, share=1, write=1)
        frappe.set_user(OWNER)
        self.assertFalse(frappe.db.get_value("Drive Permission", {"entity": self.folder.name, "user": OTHER}, "write"))

    def test_missing_entity_is_rejected(self):
        with self.assertRaises(ValueError):
            call("does-not-exist", "rename", new_title="x")

    def test_methods_are_only_available_through_call_controller_method(self):
        call(self.folder.name, "share", user=OTHER, read=1)
        frappe.set_user(OTHER)
        for method in ("rename", "share", "unshare", "change_color"):
            with self.subTest(method=method), self.assertRaises(frappe.PermissionError):
                run_doc_method(method, dt="Drive File", dn=self.folder.name, args={"new_title": "x"})
