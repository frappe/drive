# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet
import frappe.share
from pathlib import Path
import shutil
from werkzeug.utils import secure_filename
from drive.utils.files import get_entity_path, get_user_directory_path

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
		elif self.flags.save_path:
			path = self.flags.save_path
			shutil.rmtree(path) if self.is_group else path.unlink()


	def move(self, destination_folder):
		dest_is_group = frappe.db.get_value('Drive Entity', destination_folder, 'is_group')
		if not dest_is_group:
			raise NotADirectoryError('Destination is not a folder')
		source_path = get_entity_path(self.name)
		destination_path = get_entity_path(destination_folder)
		if (destination_path / source_path.name).exists():
			raise FileExistsError()
		shutil.move(source_path, destination_path)
		self.parent_drive_entity = destination_folder
		self.flags.moved_path = destination_path / source_path.name
		frappe.local.rollback_observers.append(self)
		self.save()


	def move_to_root(self):
		source_path = get_entity_path(self.name)
		destination_path = get_user_directory_path()
		if (destination_path / source_path.name).exists():
			raise FileExistsError()
		shutil.move(source_path, destination_path)
		self.parent_drive_entity = ''
		self.flags.moved_path = destination_path / source_path.name
		frappe.local.rollback_observers.append(self)
		self.save()


	def rename(self, new_title):
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
