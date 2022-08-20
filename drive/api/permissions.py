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
			'share_name': entity_name
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
	:return: List of DriveEntities with permissions
	:rtype: list[frappe._dict]
	"""

	if entity_name:
		doc = frappe.get_doc('Drive Entity', entity_name)
		if not doc.is_group:
			frappe.throw('Specified entity is not a folder', NotADirectoryError)
		# Fix this
		if not frappe.has_permission(doctype='Drive Entity', doc=entity_name, ptype='read', user=frappe.session.user) and doc.general_access == 'restricted':
			frappe.throw('Cannot access folder due to insufficient permissions', frappe.PermissionError)
		x = frappe.db.get_list('Drive Entity',
			filters={
				'parent_drive_entity': entity_name,
				'general_access': ['!=', 'restricted'],
				'is_active': 1
			},
		)
		print(x)
		return x

	DocShare = frappe.qb.DocType('DocShare')
	DriveEntity = frappe.qb.DocType('Drive Entity')
	query = (
		frappe.qb.from_(DocShare)
		.inner_join(DriveEntity)
		.on(
			(DocShare.share_name == DriveEntity.name) &
			(DocShare.user == frappe.session.user)
		)
		.select(
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
			DocShare.share
		)
		.where(DriveEntity.is_active == 1)
	)

	if entity_name:
		query = query.where(DriveEntity.parent_drive_entity == entity_name)
		return query.run(as_dict=True)
	else:
		result = query.run(as_dict=True)
		names = [x.name for x in result]
		return filter(lambda x: x.parent_drive_entity not in names, result) # To only return highest level entity
