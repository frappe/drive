# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet
from pathlib import Path
import shutil
from drive.utils.files import get_user_directory

class DriveEntity(NestedSet):
	nsm_parent_field = 'parent_drive_entity'
	def on_update(self):
		super().on_update()


	def before_save(self):
		self.version = self.version + 1


	def on_trash(self):
		if self.is_group:
			for child in self.get_children():
				child.delete()
		super().on_trash()


	def after_delete(self):
		"""Remove file once document is deleted"""
		if self.path:
			path = Path(self.path)
			path.unlink()


	def on_rollback(self):
		if self.flags.file_created:
			shutil.rmtree(self.path) if self.is_group else self.path.unlink()


	def move(self, new_parent=None):
		"""
		Move file or folder to the new parent folder

		:param new_parent: Document-name of the new parent folder. Defaults to the user directory
		:raises NotADirectoryError: If the new_parent is not a folder, or does not exist
		:raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
		:return: DriveEntity doc once file is moved
		"""

		new_parent = new_parent or get_user_directory().name
		is_group = frappe.db.get_value('Drive Entity', new_parent, 'is_group')
		if not is_group:
			raise NotADirectoryError()
		entity_exists = frappe.db.exists({
			'doctype': 'Drive Entity',
			'parent_drive_entity': new_parent,
			'title': self.title
		})
		if entity_exists:
			raise FileExistsError()
		self.parent_drive_entity = new_parent
		self.save()
		return self


	def rename(self, new_title):
		"""
		Rename file or folder

		:param new_title: New file or folder name
		:raises FileExistsError: If a file or folder with the same name already exists in the parent folder
		:return: DriveEntity doc once it's renamed
		"""

		entity_exists = frappe.db.exists({
			'doctype': 'Drive Entity',
			'parent_drive_entity': self.parent_drive_entity,
			'title': new_title
		})
		if entity_exists:
			raise FileExistsError()

		self.title = new_title
		self.save()
		return self


	def share(self, user, write=0, share=0, notify=1):
		"""
		Share this file or folder with the specified user.
		If it has already been shared, update permissions.

		:param user: User with whom this is to be shared
		:param write: 1 if write permission is to be granted. Defaults to 0
		:param share: 1 if share permission is to be granted. Defaults to 0
		:param notify: 1 if the user should be notified. Defaults to 1
		"""

		if self.is_group:
			for child in self.get_children():
				child.share(user, write, share, 0)
			frappe.share.add('Drive Entity', self.name, user, write=write, share=share, notify=notify)
		else:
			frappe.share.add('Drive Entity', self.name, user, write=write, share=share, notify=notify)


	def unshare(self, user):
		"""Unshare this file or folder with the specified user"""

		if self.is_group:
			for child in self.get_children():
				child.unshare(user)
			frappe.share.remove('Drive Entity', self.name, user)
		else:
			frappe.share.remove('Drive Entity', self.name, user)


	@frappe.whitelist()
	def list_folder_contents(self, fields=None, order_by='title'):
		"""
		Return list of DriveEntity records present in this folder

		:param fields: List of doc-fields that should be returned. Defaults to ['name', 'title', 'is_group', 'owner', 'modified', 'file_size']
		:param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
		:raises NotADirectoryError: If this DriveEntity doc is not a folder
		:return: List of DriveEntity records
		:rtype: list
		"""

		if not self.is_group:
			raise NotADirectoryError
		fields = fields or ['name', 'title', 'is_group', 'owner', 'modified', 'file_size']
		return frappe.db.get_list('Drive Entity',
			filters={
				'parent_drive_entity': self.name
			},
			fields=fields,
			order_by=order_by
		)