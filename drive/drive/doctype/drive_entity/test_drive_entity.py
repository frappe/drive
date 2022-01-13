# Copyright (c) 2021, mituldavid and Contributors
# See license.txt

import frappe
import unittest
from werkzeug.utils import secure_filename
from drive.api.files import create_folder
from drive.utils.files import get_save_path, get_entity_path

def create_text_file(parent, filename):
	save_path = get_save_path(parent, filename)
	with open(save_path, "w") as f:
		f.write("This is a test file")
	drive_entity_doc = frappe.get_doc({
		'doctype': 'Drive Entity',
		'parent_drive_entity': parent,
		'title': secure_filename(filename),
		'file_size': save_path.stat().st_size,
		'mime_type': 'text/plain'
	})
	drive_entity_doc.flags.save_path = save_path
	frappe.local.rollback_observers.append(drive_entity_doc)
	drive_entity_doc.save()
	return drive_entity_doc


class TestDriveEntity(unittest.TestCase):
	def setUp(self):
		self.test_folder1_doc = create_folder('', 'TestFolder1')
		self.test_file1_doc = create_text_file('', 'Test1.txt')
		self.test_file2_doc = create_text_file(self.test_folder1_doc.name, 'Test2.txt')


	def test_simple_move(self):
		original_path = get_entity_path(self.test_file1_doc.name)
		self.test_file1_doc.move(self.test_folder1_doc.name)
		moved_path = get_entity_path(self.test_file1_doc.name)
		self.assertNotEqual(original_path, moved_path)
		self.assertEqual(moved_path.parent, get_entity_path(self.test_folder1_doc.name))
		self.assertFalse(original_path.exists())
		self.assertTrue(moved_path.exists())


	def test_move_to_file(self):
		original_path = get_entity_path(self.test_file1_doc.name)
		with self.assertRaises(NotADirectoryError):
			self.test_file1_doc.move(self.test_file2_doc.name)
		moved_path = get_entity_path(self.test_file1_doc.name)
		self.assertTrue(original_path.exists())
		self.assertEqual(original_path, moved_path)


	def test_move_to_non_existent_dest(self):
		original_path = get_entity_path(self.test_file1_doc.name)
		with self.assertRaises(NotADirectoryError):
			self.test_file1_doc.move('test')
		moved_path = get_entity_path(self.test_file1_doc.name)
		self.assertTrue(original_path.exists())
		self.assertEqual(original_path, moved_path)


	def tearDown(self):
		self.test_folder1_doc.delete()
		self.test_file1_doc.delete()
		self.test_file2_doc.delete()
