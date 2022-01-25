# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from pathlib import Path
import uuid
import mimetypes
from drive.utils.files import get_user_directory, create_user_directory

@frappe.whitelist()
def upload_file():
	"""
	Accept chunked file contents via a multipart upload, store the file on
	disk, and insert a corresponding DriveEntity doc.

	:param file: Request object containing uploaded chunks
	:param parent: Document-name of the parent folder. Defaults to the user directory
	:param chunk_index: Index of chunk present in the current upload request
	:param total_chunk_count: Total number of chunks for the file
	:param chunk_byte_offset: Position in the file at which the current chunk starts
	:param total_file_size: Total size of the file in bytes
	:raises FileExistsError: If a file with the same name already exists in the specified parent folder
	:raises ValueError: If file is not present in the request
	:raises ValueError: If the size of the stored file does not match the specified filesize
	:return: DriveEntity doc once entire file has been uploaded
	"""

	file = frappe.request.files['file']
	if not file:
		raise ValueError('File is not present in the request')

	try:
		user_directory = get_user_directory()
	except FileNotFoundError:
		user_directory = create_user_directory()

	parent = frappe.form_dict.parent or user_directory.name
	current_chunk = int(frappe.form_dict.chunk_index)
	total_chunks = int(frappe.form_dict.total_chunk_count)
	entity_exists = frappe.db.exists({
		'doctype': 'Drive Entity',
		'parent_drive_entity': parent,
		'title': file.filename
	})
	save_path = Path(user_directory.path) / f'{parent}_{file.filename}'

	if current_chunk == 0 and (entity_exists or save_path.exists()):
		raise FileExistsError()
	with open(save_path, 'ab') as f:
		f.seek(int(frappe.form_dict.chunk_byte_offset))
		f.write(file.stream.read())

	if current_chunk + 1 == total_chunks:
		file_size = save_path.stat().st_size
		if file_size != int(frappe.form_dict.total_file_size):
			save_path.unlink()
			raise ValueError('Size on disk does not match the specified filesize')
		else:
			mime_type, encoding = mimetypes.guess_type(save_path)
			name = uuid.uuid4().hex
			path = save_path.parent / f'{name}{save_path.suffix}'
			save_path.rename(path)
			drive_entity = frappe.get_doc({
				'doctype': 'Drive Entity',
				'name': name,
				'title': file.filename,
				'parent_drive_entity': parent,
				'path': path,
				'file_size': file_size,
				'mime_type': mime_type
			})
			drive_entity.flags.file_created = True
			frappe.local.rollback_observers.append(drive_entity)
			drive_entity.insert()
			return drive_entity


@frappe.whitelist()
def create_folder(title, parent=None):
	"""
	Create a new folder.

	:param title: Folder name
	:param parent: Document-name of the parent folder. Defaults to the user directory
	:raises FileExistsError: If a folder with the same name already exists in the specified parent folder
	:return: DriveEntity doc of the new folder
	"""

	try:
		user_directory = get_user_directory()
	except FileNotFoundError:
		user_directory = create_user_directory()

	parent = parent or user_directory.name
	entity_exists = frappe.db.exists({
		'doctype': 'Drive Entity',
		'parent_drive_entity': parent,
		'title': title
	})
	if entity_exists:
		raise FileExistsError('Folder already exists')

	drive_entity = frappe.get_doc({
		'doctype': 'Drive Entity',
		'name': uuid.uuid4().hex,
		'title': title,
		'is_group': 1,
		'parent_drive_entity': parent,
	})
	drive_entity.insert()
	return drive_entity