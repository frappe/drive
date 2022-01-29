# Copyright (c) 2021, mituldavid and Contributors
# See license.txt

import frappe
from frappe.utils import get_site_url
import unittest
import json
import requests
from pathlib import Path
from drive.utils.files import get_user_directory
from drive.api.files import create_folder

class TestUploadAPI(unittest.TestCase):
	BASE_URL = get_site_url(frappe.local.site)

	@property
	def sid(self):
		if not getattr(self, '_sid', None):
			self._sid = requests.post(
				f'{self.BASE_URL}/api/method/login',
				data={
					'usr': 'test_drive@example.com',
					'pwd': '!@%@%$4!72$*',
				}
			).cookies.get('sid')
		return self._sid


	def POST(self, method, data, files=None):
		response = requests.post(
			f'{self.BASE_URL}/api/method/{method}?sid={self.sid}',
			data=data,
			files=files
		)
		return response


	def call_upload_file(self, file_path, parent=''):
		file_name = file_path.name
		file_size = file_path.stat().st_size
		chunk_size = file_size // 2
		# ceil division to calculate total_chunk_count
		total_chunk_count = - (file_size // - chunk_size)
		index = 0
		with open(file_path, 'rb') as f:
			while True:
				chunk = f.read(chunk_size)
				if not chunk:
					return response

				response = self.POST(
					'drive.api.files.upload_file',
					data={
						'parent': parent,
						'chunk_index': index,
						'total_chunk_count': total_chunk_count,
						'chunk_byte_offset': index * chunk_size,
						'total_file_size': file_size
					},
					files={
						'file': (file_name, chunk)
					}
				)
				if response.status_code != requests.codes.ok:
					return response
				index = index + 1


	def test_upload_file(self):
		file_path = Path(frappe.get_app_path('drive')) / 'tests' / 'fixtures' / 'sample_text_file.txt'
		response = self.call_upload_file(file_path)
		response_message = json.loads(response.content.decode()).get('message')
		self.assertIsNotNone(response_message)
		self.assertEqual(response_message.get('title'), 'sample_text_file.txt')
		self.assertEqual(response_message.get('file_size'), file_path.stat().st_size)
		self.assertEqual(response_message.get('parent_drive_entity'), get_user_directory('test_drive@example.com').name)
		self.assertTrue(Path(response_message.get('path')).exists())
		frappe.delete_doc_if_exists('Drive Entity', response_message['name'])


	def test_upload_without_file(self):
		response = self.POST(
			'drive.api.files.upload_file',
			data={
				'chunk_index': 0,
				'total_chunk_count': 1,
				'chunk_byte_offset': 0,
				'total_file_size': 1024
			}
		)
		self.assertEqual(response.status_code, 400)


	def test_upload_with_inaccurate_file_size(self):
		file_path = Path(frappe.get_app_path('drive')) / 'tests' / 'fixtures' / 'sample_text_file.txt'
		with open(file_path, 'rb') as f:
			response = self.POST(
				'drive.api.files.upload_file',
				data={
					'chunk_index': 0,
					'total_chunk_count': 1,
					'chunk_byte_offset': 0,
					'total_file_size': 1024,
				},
				files={
					'file': ('sample_text_file.txt', f)
				}
			)
		self.assertEqual(response.status_code, 500)