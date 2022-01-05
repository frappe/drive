# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet, get_ancestors_of, get_descendants_of
from pathlib import Path
import shutil
from werkzeug.utils import secure_filename
import hashlib
import mimetypes

class DriveEntity(NestedSet):
	nsm_parent_field = 'parent_drive_entity'
	def on_update(self):
		self.version = self.version + 1
		super().on_update()


	def on_trash(self):
		if self.is_group:
			for child in self.get_children():
				child.delete()
			path = get_entity_path(self.name)
			shutil.rmtree(path)
		else:
			path = get_entity_path(self.name)
			path.unlink()
		super().on_trash(True)


	def on_rollback(self):
		if self.flags.moved_path:
			shutil.move(self.flags.moved_path, get_entity_path(self.name))
		elif self.flags.changed_name:
			changed_path = self.flags.changed_name
			changed_path.rename(get_entity_path(self.name))
		else:
			self.flags.on_rollback = True
			self.on_trash()


	def move_entity(self, destination_folder):
		dest_is_group = frappe.db.get_value('Drive Entity', destination_folder, 'is_group')
		if not dest_is_group:
			raise NotADirectoryError('Destination is not a folder')
		source_path = get_entity_path(self.name)
		destination_path = get_entity_path(destination_folder)
		if (destination_path / source_path.name).exists():
			raise FileExistsError()
		shutil.move(source_path, destination_path)
		self.parent_drive_entity = destination_folder
		self.flags.moved_path = destination_path
		frappe.local.rollback_observers.append(self)
		self.save()


	def move_entity_to_root(self):
		source_path = get_entity_path(self.name)
		destination_path = get_user_directory_path()
		if (destination_path / source_path.name).exists():
			raise FileExistsError()
		shutil.move(source_path, destination_path)
		self.parent_drive_entity = ''
		self.flags.moved_path = destination_path
		frappe.local.rollback_observers.append(self)
		self.save()


	def rename_entity(self, new_title):
		entity_path = get_entity_path(self.name)
		entity_extension = entity_path.suffix
		new_title = Path(secure_filename(new_title)).stem + entity_extension
		new_path = entity_path.parent / new_title
		if new_path.exists():
			raise FileExistsError()
		entity_path.rename(new_path)
		self.title = new_title
		self.flags.changed_name = new_path
		frappe.local.rollback_observers.append(self)
		self.save()


@frappe.whitelist(allow_guest=True)
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
			frappe.local.rollback_observers.append(drive_entity_doc)
			drive_entity_doc.save()
			return drive_entity_doc


@frappe.whitelist(allow_guest=True)
def create_folder(parent, folder_name):
	save_path = get_save_path(parent, folder_name)
	if parent:
		save_path = get_entity_path(parent) / folder_name
	if save_path.exists():
		raise FileExistsError('Folder already exists')
	save_path.mkdir()
	drive_entity_doc = frappe.get_doc({
		'doctype': 'Drive Entity',
		'parent_drive_entity': parent,
		'is_group': 1,
		'title': secure_filename(folder_name)
	})
	frappe.local.rollback_observers.append(drive_entity_doc)
	drive_entity_doc.save()
	return drive_entity_doc


def get_user_directory_path():
	user_directory_name = hashlib.md5(frappe.session.user.encode('utf-8')).hexdigest()
	return Path(frappe.get_site_path('private'), user_directory_name)


def get_entity_path(entity_name):
	if not frappe.db.exists('Drive Entity', entity_name):
		raise ValueError('This entity does not exist')
	path = get_user_directory_path()
	parents = get_ancestors_of('Drive Entity', entity_name, 'lft asc')
	for parent in parents:
		path = path / frappe.db.get_value('Drive Entity', parent, 'title')
	path = path / frappe.db.get_value('Drive Entity', entity_name, 'title')
	return path


def get_save_path(parent, name):
	user_directory_path = get_user_directory_path()
	if not user_directory_path.exists():
		user_directory_path.mkdir()
	name = secure_filename(name)
	save_path = user_directory_path / name
	if parent:
		save_path = get_entity_path(parent) / name
	return save_path
