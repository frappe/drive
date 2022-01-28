# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def grant_view_access(entity_name, user, notify=1):
	drive_entity_doc = frappe.get_doc('Drive Entity', entity_name)
	drive_entity_doc.share(user, notify=notify)


@frappe.whitelist()
def grant_edit_access(entity_name, user, can_share=0, notify=1):
	drive_entity_doc = frappe.get_doc('Drive Entity', entity_name)
	drive_entity_doc.share(user, write=1, share=can_share, notify=notify)


@frappe.whitelist()
def revoke_access(entity_name, user):
	drive_entity_doc = frappe.get_doc('Drive Entity', entity_name)
	drive_entity_doc.unshare(user)


@frappe.whitelist()
def get_shared_with_list(entity_name):
	"""
	Return the list of users with whom this file or folder has been shared

	:param entity_name: Document-name of this file or folder
	:raises PermissionError: If the user does not have edit permissions
	:return: List of users, with permissions and last modified datetime
	:rtype: list[frappe._dict]
	"""

	if not frappe.has_permission(doctype='Drive Entity', doc=entity_name, ptype='edit', user=frappe.session.user):
		raise frappe.PermissionError
	return frappe.db.get_list('DocShare',
		filters={
			'share_doctype': 'Drive Entity',
			'share_name': entity_name
		},
		fields=['user', 'read', 'write', 'share', 'everyone', 'modified']
	)


@frappe.whitelist()
def get_shared_with_me():
	"""
	Return the list of files and folders shared with the current user

	:return: List of DriveEntities with permissions
	:rtype: list[frappe._dict]
	"""

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
			DriveEntity.file_size,
			DocShare.read,
			DocShare.write,
			DocShare.share
		)
	)
	return query.run(as_dict=True)