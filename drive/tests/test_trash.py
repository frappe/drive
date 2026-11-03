# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from drive.api.files import remove_or_restore, create_folder
from drive.tests.utils import DriveTestCase, make_file, read_file
from drive.utils import get_home_folder
from drive.utils.files import FileManager


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
        self.assertEqual(frappe.db.get_value("Drive File", second.name, "title"), "notes (1).txt")
        self.assertEqual(read_file(second.name), "second")
        self.assertEqual(read_file(first.name), "first")

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
        manager = FileManager()
        legacy = manager.site_folder / get_home_folder(self.team)["path"] / ".trash" / "old.txt"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        (manager.site_folder / drive_file.path).rename(legacy)
        frappe.db.set_value("Drive File", drive_file.name, {"is_active": 0, "trash_path": ""})

        remove_or_restore([drive_file.name])
        self.assertEqual(read_file(drive_file.name), "old")

    def test_a_move_is_undone_when_the_transaction_rolls_back(self):
        drive_file = make_file(self.team, "draft.txt", "draft")
        manager = FileManager()
        old_path = manager.site_folder / drive_file.path
        new_path = old_path.with_name("moved.txt")

        manager.move(drive_file, new_path.relative_to(manager.site_folder))
        self.assertTrue(new_path.exists())
        frappe.db.rollback()
        self.assertTrue(old_path.exists())
        self.assertFalse(new_path.exists())

    def test_a_move_never_replaces_an_existing_file(self):
        drive_file = make_file(self.team, "a.txt", "a")
        other = make_file(self.team, "b.txt", "b")
        with self.assertRaises(FileExistsError):
            FileManager().move(drive_file, other.path)
        self.assertEqual(read_file(other.name), "b")
