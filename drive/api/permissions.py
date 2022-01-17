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

