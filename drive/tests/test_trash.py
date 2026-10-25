# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.client import insert

from drive.api.files import create_folder, remove_or_restore
from drive.tests.utils import OTHER, DriveTestCase, disk_path, make_file, read_file
from drive.utils import STATUS_TRASHED, get_home_folder
from drive.utils.files import FileManager, storage_key


class TestTrash(DriveTestCase):
    def test_trashing_two_files_with_the_same_name_keeps_both(self):
        first = make_file(self.team, "notes.txt", "first")
        remove_or_restore([first.name])
        second = make_file(self.team, "notes.txt", "second")
        remove_or_restore([second.name])

        remove_or_restore([first.name])
        self.assertEqual(read_file(first.name), "first")

        # Its name is taken now, so the second file comes back under a new one
        remove_or_restore([second.name])
        self.assertEqual(frappe.db.get_value("File", second.name, "file_name"), "notes (1).txt")
        self.assertEqual(read_file(second.name), "second")
        self.assertEqual(read_file(first.name), "first")

    def test_trashed_files_cannot_be_reached_through_site_files(self):
        drive_file = make_file(self.team, "notes.txt", "private")
        remove_or_restore([drive_file.name])
        trash_url = "/" + frappe.db.get_value("File", drive_file.name, "trash_path")

        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            insert({"doctype": "File", "file_name": "copy.txt", "file_url": trash_url, "is_private": 1})

    def test_trashing_folders_with_the_same_name_keeps_both(self):
        first = create_folder(self.team, "Reports")
        inside_first = make_file(self.team, "a.txt", "a", parent=first.name)
        remove_or_restore([first.name])
        second = create_folder(self.team, "Reports")
        make_file(self.team, "b.txt", "b", parent=second.name)
        remove_or_restore([second.name])

        remove_or_restore([first.name])
        self.assertEqual(read_file(inside_first.name), "a")

    def test_restores_items_trashed_before_trash_path_was_stored(self):
        drive_file = make_file(self.team, "old.txt", "old")
        home = storage_key(get_home_folder(self.team)["file_url"])
        legacy = FileManager().site_folder / home / ".trash" / "old.txt"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        disk_path(drive_file.name).rename(legacy)
        frappe.db.set_value("File", drive_file.name, {"status": STATUS_TRASHED, "trash_path": ""})

        remove_or_restore([drive_file.name])
        self.assertEqual(read_file(drive_file.name), "old")

    def test_a_move_is_undone_when_the_transaction_rolls_back(self):
        drive_file = make_file(self.team, "draft.txt", "draft")
        old_path = disk_path(drive_file.name)
        new_path = old_path.with_name("moved.txt")

        manager = FileManager()
        manager.move(drive_file, new_path.relative_to(manager.site_folder))
        self.assertTrue(new_path.exists())
        frappe.db.rollback()
        self.assertTrue(old_path.exists())
        self.assertFalse(new_path.exists())

    def test_a_move_never_replaces_an_existing_file(self):
        drive_file = make_file(self.team, "a.txt", "a")
        other = make_file(self.team, "b.txt", "b")
        with self.assertRaises(FileExistsError):
            FileManager().move(drive_file, other.file_url)
        self.assertEqual(read_file(other.name), "b")
