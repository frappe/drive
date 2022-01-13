# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import get_ancestors_of
from pathlib import Path
from werkzeug.utils import secure_filename
import hashlib

def get_user_directory_path(user=None):
	if not user:
		user = frappe.session.user
	user_directory_name = hashlib.md5(user.encode('utf-8')).hexdigest()
	return Path(frappe.get_site_path('private'), user_directory_name)


def get_entity_path(entity_name):
	if not frappe.db.exists('Drive Entity', entity_name):
		raise ValueError('This entity does not exist')
	owner = frappe.db.get_value('Drive Entity', entity_name, 'owner')
	path = get_user_directory_path(owner)
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
