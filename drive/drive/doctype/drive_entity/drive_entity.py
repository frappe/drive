# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet
from pathlib import Path
import shutil
from drive.utils.files import get_user_directory

class DriveEntity(NestedSet):
	nsm_parent_field = 'parent_drive_entity'
	nsm_oldparent_field = 'old_parent'
	def on_update(self):
		super().on_update()


	def before_save(self):
		self.version = self.version + 1


	def after_insert(self):
		"""Copy parent permissions to new child entity"""

		if self.parent_drive_entity is None:
			return
		permissions = frappe.share.get_users("Drive Entity", self.parent_drive_entity)
		for permission in permissions:
			frappe.share.add(
				"Drive Entity",
				self.name,
				permission.user,
				write=permission.write,
				share=permission.share,
				notify=0,
				flags={"ignore_share_permission": True}
			)


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


	@frappe.whitelist()
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


	@frappe.whitelist()
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
			frappe.throw(f"'{new_title}' already exists", FileExistsError)

		self.title = new_title
		self.save()
		return self


	@frappe.whitelist()
	def change_access(self, new_access):
		"""
		Change general sharing access for entity

		:param new_access: New access level of entity
		:return: DriveEntity doc once it's access is changed
		"""

		self.general_access = new_access
		self.save()
		if self.is_group:
			for child in self.get_children():
				child.change_access(new_access)


	@frappe.whitelist()
	def share(self, user, write=0, share=0, notify=1):
		"""
		Share this file or folder with the specified user.
		If it has already been shared, update permissions.

		:param user: User with whom this is to be shared
		:param write: 1 if write permission is to be granted. Defaults to 0
		:param share: 1 if share permission is to be granted. Defaults to 0
		:param notify: 1 if the user should be notified. Defaults to 1
		"""

		flags = {"ignore_share_permission": True} if frappe.session.user == self.owner else None
		if self.is_group:
			for child in self.get_children():
				child.share(user, write, share, 0)
			frappe.share.add('Drive Entity', self.name, user, write=write, share=share, notify=notify, flags=flags)
		else:
			frappe.share.add('Drive Entity', self.name, user, write=write, share=share, notify=notify, flags=flags)


	@frappe.whitelist()
	def unshare(self, user):
		"""Unshare this file or folder with the specified user"""

		has_share_permissions = (
			frappe.session.user == self.owner
			or frappe.has_permission("Drive Entity", ptype="share", doc=self.name)
		)
		if not has_share_permissions:
			frappe.throw(f"You do not have permissions to unshare '{self.title}'")
		flags = {"ignore_share_permission": True} if frappe.session.user == self.owner else None
		if self.is_group:
			for child in self.get_children():
				child.unshare(user)
			frappe.share.remove('Drive Entity', self.name, user, flags=flags)
		else:
			frappe.share.remove('Drive Entity', self.name, user, flags=flags)

