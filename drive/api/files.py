# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from pathlib import Path
from werkzeug.utils import secure_filename
import mimetypes
from drive.utils.files import get_save_path

@frappe.whitelist()
def upload_file():
	file = frappe.request.files['file']
	if not file:
		raise ValueError('File is not present in the request')
	parent = frappe.form_dict.parent
	save_path = get_save_path(parent, file.filename)

	current_chunk = int(frappe.form_dict.chunkindex)
	total_chunks = int(frappe.form_dict.totalchunkcount)

	if save_path.exists() and current_chunk == 0:
		raise FileExistsError()

	with open(save_path, 'ab') as f:
		f.seek(int(frappe.form_dict.chunkbyteoffset))
		f.write(file.stream.read())

	if current_chunk + 1 == total_chunks:
		file_size = save_path.stat().st_size
		if file_size != int(frappe.form_dict.totalfilesize):
			save_path.unlink()
			raise ValueError('Size on disk does not match the specified filesize')
		else:
			mime_type, encoding = mimetypes.guess_type(save_path)
			drive_entity_doc = frappe.get_doc({
				'doctype': 'Drive Entity',
				'parent_drive_entity': parent,
				'title': secure_filename(file.filename),
				'file_size': file_size,
				'mime_type': mime_type
			})
			drive_entity_doc.flags.save_path = save_path
			frappe.local.rollback_observers.append(drive_entity_doc)
			drive_entity_doc.save()
			return drive_entity_doc


@frappe.whitelist()
def create_folder(parent, folder_name):
	save_path = get_save_path(parent, folder_name)
	if save_path.exists():
		raise FileExistsError('Folder already exists')
	save_path.mkdir()
	drive_entity_doc = frappe.get_doc({
		'doctype': 'Drive Entity',
		'parent_drive_entity': parent,
		'is_group': 1,
		'title': secure_filename(folder_name)
	})
	drive_entity_doc.flags.save_path = save_path
	frappe.local.rollback_observers.append(drive_entity_doc)
	drive_entity_doc.save()
	return drive_entity_doc