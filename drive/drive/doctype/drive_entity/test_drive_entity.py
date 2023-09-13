import frappe
import unittest
import uuid
from pathlib import Path
from drive.api.files import create_folder
from drive.utils.files import get_user_directory


def create_text_file(filename, parent=None):
    try:
        user_directory = get_user_directory()
    except FileNotFoundError:
        user_directory = create_user_directory()
    parent = parent or user_directory.name
    name = uuid.uuid4().hex
    path = Path(user_directory.path) / f"{name}.txt"
    with open(path, "w") as f:
        f.write("This is a test file")
    drive_entity = frappe.get_doc(
        {
            "doctype": "Drive Entity",
            "name": name,
            "title": filename,
            "parent_drive_entity": parent,
            "path": path,
            "file_size": path.stat().st_size,
            "mime_type": "text/plain",
        }
    )
    drive_entity.flags.file_created = True
    frappe.local.rollback_observers.append(drive_entity)
    drive_entity.insert()
    return drive_entity


class TestDriveEntity(unittest.TestCase):
    def setUp(self):
        self.test_file1 = create_text_file("Test1.txt")
        self.test_folder1 = create_folder("TestFolder1")
        self.test_file2 = create_text_file("Test2.txt", self.test_folder1.name)

    def test_simple_move(self):
        self.test_file1.move(self.test_folder1.name)
        self.assertEqual(self.test_file1.parent_drive_entity, self.test_folder1.name)

    def test_move_to_user_directory(self):
        self.test_file2.move()
        self.assertEqual(self.test_file2.parent_drive_entity, get_user_directory().name)

    def test_move_to_file(self):
        with self.assertRaises(NotADirectoryError):
            self.test_file1.move(self.test_file2.name)

    def test_move_to_non_existent_dest(self):
        with self.assertRaises(NotADirectoryError):
            self.test_file1.move("test")

    def test_move_to_same_parent_folder(self):
        with self.assertRaises(FileExistsError):
            self.test_file2.move(self.test_folder1.name)

    def test_simple_rename(self):
        self.test_file1.rename("renamed_file.txt")
        self.assertEqual(self.test_file1.title, "renamed_file.txt")

    def test_rename_to_existing(self):
        self.test_file1.move(self.test_folder1.name)
        with self.assertRaises(FileExistsError):
            self.test_file1.rename(self.test_file2.title)

    def test_version_update(self):
        prev_version_no = self.test_file1.version
        self.test_file1.rename("renamed_file.txt")
        self.assertEqual(self.test_file1.version, prev_version_no + 1)

    def test_share_file(self):
        self.assertFalse(frappe.has_permission(doc=self.test_file1, user="test_drive@example.com"))
        self.test_file1.share("test_drive@example.com")
        self.assertTrue(frappe.has_permission(doc=self.test_file1, user="test_drive@example.com"))

    def test_share_folder(self):
        self.assertFalse(
            frappe.has_permission(doc=self.test_folder1, user="test_drive@example.com")
        )
        self.assertFalse(frappe.has_permission(doc=self.test_file2, user="test_drive@example.com"))
        self.test_folder1.share("test_drive@example.com")
        self.assertTrue(
            frappe.has_permission(doc=self.test_folder1, user="test_drive@example.com")
        )
        self.assertTrue(frappe.has_permission(doc=self.test_file2, user="test_drive@example.com"))

    def test_share_options(self):
        self.assertFalse(
            frappe.has_permission(doc=self.test_file1, ptype="read", user="test_drive@example.com")
        )
        self.assertFalse(
            frappe.has_permission(
                doc=self.test_file1, ptype="write", user="test_drive@example.com"
            )
        )
        self.assertFalse(
            frappe.has_permission(
                doc=self.test_file1, ptype="share", user="test_drive@example.com"
            )
        )
        self.test_file1.share("test_drive@example.com", write=1, share=1)
        self.assertTrue(
            frappe.has_permission(doc=self.test_file1, ptype="read", user="test_drive@example.com")
        )
        self.assertTrue(
            frappe.has_permission(
                doc=self.test_file1, ptype="write", user="test_drive@example.com"
            )
        )
        self.assertTrue(
            frappe.has_permission(
                doc=self.test_file1, ptype="share", user="test_drive@example.com"
            )
        )

    def test_unshare_file(self):
        self.test_file1.share("test_drive@example.com")
        self.assertTrue(frappe.has_permission(doc=self.test_file1, user="test_drive@example.com"))
        self.test_file1.unshare("test_drive@example.com")
        self.assertFalse(frappe.has_permission(doc=self.test_file1, user="test_drive@example.com"))

    def test_unshare_folder(self):
        self.test_folder1.share("test_drive@example.com")
        self.assertTrue(
            frappe.has_permission(doc=self.test_folder1, user="test_drive@example.com")
        )
        self.assertTrue(frappe.has_permission(doc=self.test_file2, user="test_drive@example.com"))
        self.test_folder1.unshare("test_drive@example.com")
        self.assertFalse(
            frappe.has_permission(doc=self.test_folder1, user="test_drive@example.com")
        )
        self.assertFalse(frappe.has_permission(doc=self.test_file2, user="test_drive@example.com"))

    def test_delete_file(self):
        self.assertTrue(Path(self.test_file1.path).exists())
        self.test_file1.delete()
        self.assertFalse(frappe.db.exists("Drive Entity", self.test_file1.name))
        self.assertFalse(Path(self.test_file1.path).exists())

    def test_delete_folder(self):
        self.assertTrue(Path(self.test_file2.path).exists())
        self.test_folder1.delete()
        self.assertFalse(frappe.db.exists("Drive Entity", self.test_folder1.name))
        self.assertFalse(frappe.db.exists("Drive Entity", self.test_file2.name))
        self.assertFalse(Path(self.test_file2.path).exists())

    def tearDown(self):
        self.test_folder1.delete()
        self.test_file1.delete()
        self.test_file2.delete()
