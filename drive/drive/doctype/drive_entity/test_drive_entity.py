# Copyright (c) 2021, mituldavid and Contributors
# See license.txt

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
	path = Path(user_directory.path) / f'{name}.txt'
	with open(path, "w") as f:
		f.write("This is a test file")
	drive_entity = frappe.get_doc({
		'doctype': 'Drive Entity',
		'name': name,
		'title': filename,
		'parent_drive_entity': parent,
		'path': path,
		'file_size': path.stat().st_size,
		'mime_type': 'text/plain'
	})
	drive_entity.flags.file_created = True
	frappe.local.rollback_observers.append(drive_entity)
	drive_entity.insert()
	return drive_entity


class TestDriveEntity(unittest.TestCase):
	def setUp(self):
		self.test_file1 = create_text_file('Test1.txt')
		self.test_folder1 = create_folder('TestFolder1')
		self.test_file2 = create_text_file('Test2.txt', self.test_folder1.name)


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
			self.test_file1.move('test')


	def test_move_to_same_parent_folder(self):
		with self.assertRaises(FileExistsError):
			self.test_file2.move(self.test_folder1.name)


	def tearDown(self):
		self.test_folder1.delete()
		self.test_file1.delete()
		self.test_file2.delete()
