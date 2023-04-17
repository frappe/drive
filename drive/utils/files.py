# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
import os
from pathlib import Path
import hashlib


def create_user_directory():
    """
    Create user directory on disk, and insert corresponding DriveEntity doc

    :raises FileExistsError: If user directory already exists
    :return: Dictionary containing the document-name and path
    :rtype: frappe._dict
    """

    user_directory_name = _get_user_directory_name()
    user_directory_path = Path(frappe.get_site_path("private"), user_directory_name)
    user_directory_path.mkdir(exist_ok=False)

    full_name = frappe.get_value("User", frappe.session.user, "full_name")
    user_directory = frappe.get_doc(
        {
            "doctype": "Drive Entity",
            "name": user_directory_name,
            "title": f"{full_name}'s Drive",
            "is_group": 1,
            "path": user_directory_path,
        }
    )
    user_directory.flags.file_created = True
    frappe.local.rollback_observers.append(user_directory)
    user_directory.insert()
    return frappe._dict({"name": user_directory.name, "path": user_directory.path})


def get_user_directory(user=None):
    """
    Return the document-name, and path of the specified user's user directory

    :param user: User whose directory details should be returned. Defaults to the current user
    :raises FileNotFoundError: If user directory does not exist
    :return: Dictionary containing the document-name and path
    :rtype: frappe._dict
    """

    user_directory_name = _get_user_directory_name(user)
    user_directory = frappe.db.get_value(
        "Drive Entity", user_directory_name, ["name", "path"], as_dict=1
    )
    if user_directory is None:
        raise FileNotFoundError("User directory does not exist")
    return user_directory


def _get_user_directory_name(user=None):
    """Returns user directory name from user's unique id"""
    if not user:
        user = frappe.session.user
    return hashlib.md5(user.encode("utf-8")).hexdigest()


frappe.whitelist()


def get_new_title(entity, parent_name):
    """
    Returns new title for an entity if same title exists for another entity at the same level

    :param entity_title: Title of entity to be renamed (if at all)
    :param parent_entity: Parent entity of entity to be renamed (if at all)
    :return: String with new title
    """

    entity_title, entity_ext = os.path.splitext(entity)
    sibling_entity_titles = frappe.db.get_list(
        "Drive Entity",
        filters={
            "parent_drive_entity": parent_name,
            "title": ["like", f"{entity_title}%{entity_ext}"],
        },
        pluck="title",
    )

    if entity not in sibling_entity_titles:
        return entity

    i = 1
    while True:
        new_title = f"{entity_title} ({i}){entity_ext}"
        if new_title not in sibling_entity_titles:
            return new_title
        i += 1
