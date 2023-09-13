import frappe
import unittest
import filecmp
from unittest.mock import MagicMock
from pathlib import Path
from drive.api.files import upload_file, create_folder, get_file_content
from drive.utils.files import get_user_directory
from drive.locks.distributed_lock import DistributedLock, FileLockedError


def read_in_chunks(file_obj, chunk_size):
    chunk_index = 0
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield chunk_index, chunk
        chunk_index += 1


class TestFilesAPI(unittest.TestCase):
    def mock_chunked_upload_request(
        self, file_path, file_size, parent="", chunk_size=None, total_file_size=None
    ):
        chunk_size = chunk_size or file_size // 4
        # ceil division to calculate total_chunk_count
        total_chunk_count = -(file_size // -chunk_size)
        f = open(file_path, "rb")

        for chunk_index, chunk in read_in_chunks(f, chunk_size):
            # mock request object and form_dict
            frappe.local.request = MagicMock()
            frappe.local.request.files["file"] = MagicMock()
            frappe.local.request.files["file"].stream.read.return_value = chunk
            frappe.local.request.files["file"].filename = file_path.name
            frappe.form_dict = MagicMock()
            frappe.form_dict = frappe._dict(
                {
                    "parent": parent,
                    "chunk_index": chunk_index,
                    "total_chunk_count": total_chunk_count,
                    "chunk_byte_offset": chunk_index * chunk_size,
                    "total_file_size": total_file_size or file_size,
                }
            )
            response = upload_file()
        f.close()
        return response

    def test_upload_file(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size)
        self.assertEqual(doc.title, file_path.name)
        self.assertEqual(doc.file_size, file_size)
        self.assertEqual(doc.parent_drive_entity, get_user_directory().name)
        self.assertTrue(Path(doc.path).exists())
        self.assertTrue(filecmp.cmp(file_path, Path(doc.path), shallow=False))
        doc.delete()

    def test_single_chunk_upload(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size, chunk_size=file_size)
        self.assertEqual(doc.title, file_path.name)
        self.assertEqual(doc.file_size, file_size)
        self.assertEqual(doc.parent_drive_entity, get_user_directory().name)
        self.assertTrue(Path(doc.path).exists())
        self.assertTrue(filecmp.cmp(file_path, Path(doc.path), shallow=False))
        doc.delete()

    def test_upload_with_inaccurate_file_size(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        with self.assertRaises(ValueError):
            doc = self.mock_chunked_upload_request(file_path, file_size, total_file_size=1024)

    def test_upload_existing_file(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size)
        with self.assertRaises(FileExistsError):
            self.mock_chunked_upload_request(file_path, file_size)
        doc.delete()

    def test_create_folder(self):
        doc = create_folder("Test Folder")
        self.assertEqual(doc.is_group, 1)
        self.assertEqual(doc.title, "Test Folder")
        self.assertEqual(doc.parent_drive_entity, get_user_directory().name)
        doc.delete()

    def test_create_folder_in_parent(self):
        L1_folder = create_folder("Test Folder L1")
        self.assertEqual(L1_folder.is_group, 1)
        L2_folder = create_folder("Test Folder L2", parent=L1_folder.name)
        self.assertEqual(L2_folder.is_group, 1)
        self.assertEqual(L2_folder.title, "Test Folder L2")
        self.assertEqual(L2_folder.parent_drive_entity, L1_folder.name)
        L1_folder.delete()
        L2_folder.delete()

    def test_create_existing_folder(self):
        folder = create_folder("Test Folder")
        self.assertEqual(folder.is_group, 1)
        with self.assertRaises(FileExistsError):
            create_folder("Test Folder")
        folder.delete()

    def test_get_file_content(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size, chunk_size=file_size)
        file_content = get_file_content(doc.name)
        headers = file_content.headers
        self.assertEqual(file_content.status_code, 200)
        self.assertEqual(file_content.content_length, file_size)
        self.assertEqual(file_content.content_type, "text/plain; charset=utf-8")
        self.assertEqual(
            headers.get("Content-Disposition"), "inline; filename=sample_text_file.txt"
        )
        doc.delete()

    def test_download_file(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size, chunk_size=file_size)
        file_content = get_file_content(doc.name, trigger_download=1)
        headers = file_content.headers
        self.assertEqual(file_content.status_code, 200)
        self.assertEqual(file_content.content_length, file_size)
        self.assertEqual(file_content.content_type, "text/plain; charset=utf-8")
        self.assertEqual(
            headers.get("Content-Disposition"),
            "attachment; filename=sample_text_file.txt",
        )
        doc.delete()

    def test_get_non_existent_file_content(self):
        with self.assertRaises(ValueError):
            file_content = get_file_content("test")

    def test_get_content_of_folder(self):
        folder = create_folder("Test Folder")
        with self.assertRaises(ValueError):
            file_content = get_file_content(folder.name)
        folder.delete()

    def test_unauthorized_get_file_content(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size, chunk_size=file_size)
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            file_content = get_file_content(doc.name)
        frappe.set_user("Administrator")
        doc.delete()

    def test_get_locked_file_content(self):
        file_path = (
            Path(frappe.get_app_path("drive")) / "tests" / "fixtures" / "sample_text_file.txt"
        )
        file_size = file_path.stat().st_size
        doc = self.mock_chunked_upload_request(file_path, file_size, chunk_size=file_size)
        with DistributedLock(doc.path, exclusive=True):
            with self.assertRaises(FileLockedError):
                file_content = get_file_content(doc.name)
        doc.delete()
