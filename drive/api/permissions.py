# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def get_shared_with_list(entity_name):
	"""
	Return the list of users with whom this file or folder has been shared

	:param entity_name: Document-name of this file or folder
	:raises PermissionError: If the user does not have edit permissions
	:return: List of users, with permissions and last modified datetime
	:rtype: list[frappe._dict]
	"""

	if not frappe.has_permission(doctype='Drive Entity', doc=entity_name, ptype='write', user=frappe.session.user):
		raise frappe.PermissionError
	users = frappe.db.get_list('DocShare',
		filters={
			'share_doctype': 'Drive Entity',
			'share_name': entity_name,
			'everyone': 0,
			'user': ['!=', frappe.session.user]
		},
		fields=['user', 'read', 'write', 'share', 'everyone', 'modified']
	)
	for user in users:
		user_info = frappe.db.get_value("User", user.user, ["user_image", "full_name"], as_dict=True)
		user.update(user_info)
	
	return users


@frappe.whitelist()
def get_shared_with_me(entity_name=None):
	"""
	Return the list of files and folders shared with the current user

	:param entity_name: Document-name of the folder whose contents are to be listed.
	:raises NotADirectoryError: If this DriveEntity doc is not a folder
	:return: List of DriveEntities with permissions
	:rtype: list[frappe._dict]
	"""

	DocShare = frappe.qb.DocType('DocShare')
	DriveEntity = frappe.qb.DocType('Drive Entity')
	selectedFields = [
		DriveEntity.name,
		DriveEntity.title,
		DriveEntity.is_group,
		DriveEntity.owner,
		DriveEntity.modified,
		DriveEntity.creation,
		DriveEntity.file_size,
		DriveEntity.mime_type,
		DriveEntity.parent_drive_entity,
		DocShare.read,
		DocShare.write,
		DocShare.everyone,
		DocShare.share
	]

	if entity_name:
		is_group, is_active = frappe.db.get_value('Drive Entity', entity_name, ['is_group', 'is_active'])
		if not is_group:
			frappe.throw('Specified entity is not a folder', NotADirectoryError)
		if not is_active:
			frappe.throw('Specified folder has been trashed by the owner')
		if not frappe.has_permission(doctype='Drive Entity', doc=entity_name, ptype='read', user=frappe.session.user):
			frappe.throw('Cannot access folder due to insufficient permissions', frappe.PermissionError)
		query = (
			frappe.qb.from_(DocShare)
			.inner_join(DriveEntity)
			.on((DocShare.share_name == DriveEntity.name))
			.select(*selectedFields)
			.where(
				(DriveEntity.is_active == 1) &
				(DriveEntity.parent_drive_entity == entity_name) &
				((DocShare.user == frappe.session.user) | (DocShare.everyone == 1))
			)
		)
		result = query.run(as_dict=True)
		user_specific_items = list(filter(lambda x: not x.everyone, result))
		names = [x.name for x in user_specific_items]
		open_access_items = list(filter(lambda x: x.name not in names, result))
		return user_specific_items + open_access_items # Return unique values

	query = (
		frappe.qb.from_(DocShare)
		.inner_join(DriveEntity)
		.on(
			(DocShare.share_name == DriveEntity.name) &
			(DocShare.user == frappe.session.user)
		)
		.select(*selectedFields)
		.where(DriveEntity.is_active == 1) 
	)
	result = query.run(as_dict=True)
	names = [x.name for x in result]
	return filter(lambda x: x.parent_drive_entity not in names and x.owner != frappe.session.user, result) # Return highest level entity


@frappe.whitelist()
def get_general_access(entity_name):
	"""
	Return the general access permissions for the given entity

	:param entity_name: Document-name of the entity whose permissions are to be fetched
	:return: Dict of general access permissions (read, write)
	:rtype: frappe._dict or None
	"""


	return frappe.db.get_value('DocShare',
	{ 'share_name': entity_name, 'everyone': 1 },
	[ 'read', 'write' ],
	as_dict=1
	)


@frappe.whitelist()
def get_user_access(entity_name):
	"""
	Return the user specific access permissions for an entity if it exists or general access permissions

	:param entity_name: Document-name of the entity whose permissions are to be fetched
	:return: Dict of general access permissions (read, write)
	:rtype: frappe._dict or None
	"""


	user_access = frappe.db.get_value('DocShare',
	{ 'share_name': entity_name, 'user': frappe.session.user },
	[ 'read', 'write' ],
	as_dict=1
	)

	if user_access:
		return user_access

	return get_general_access(entity_name)