# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet, get_ancestors_of
from pathlib import Path
import shutil
import uuid
from drive.utils.files import get_user_directory, create_user_directory


class DriveEntity(NestedSet):
    nsm_parent_field = 'parent_drive_entity'
    nsm_oldparent_field = 'old_parent'

    def on_update(self):
        super().on_update()

    def before_save(self):
        self.version = self.version + 1

    # def get_children(self):
    # 	if int(frappe.__version__.split('.')[0]) >= 14:
    # 		super().get_children(self)
    # 	else:
    # 		child_names = frappe.get_list(
    # 			self.doctype, filters={self.nsm_parent_field: self.name}, pluck="name"
    # 		)
    # 		for name in child_names:
    # 			yield frappe.get_doc(self.doctype, name)

    def after_insert(self):
        """Copy parent permissions to new child entity"""

        if self.parent_drive_entity is None:
            return
        permissions = frappe.share.get_users(
            "Drive Entity", self.parent_drive_entity)
        for permission in permissions:
            frappe.share.add_docshare(
                "Drive Entity",
                self.name,
                permission.user,
                write=permission.write,
                share=permission.share,
                everyone=permission.everyone,
                notify=0,
                flags={"ignore_share_permission": True}
            )

    def on_trash(self):
        frappe.db.delete("Drive Favourite", {
            "entity": self.name
        })
        if self.is_group:
            for child in self.get_children():
                has_write_access = frappe.has_permission(
                    doctype='Drive Entity', doc=self, ptype='write', user=frappe.session.user)
                child.delete(ignore_permissions=has_write_access)
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
        self.parent_drive_entity = new_parent
        self.save()
        return self

    @frappe.whitelist()
    def copy(self, new_parent=None, parent_user_directory=None):
        """
        Copy file or folder along with its contents to the new parent folder

        :param new_parent: Document-name of the new parent folder. Defaults to the user directory
        :raises NotADirectoryError: If the new_parent is not a folder, or does not exist
        :raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
        """

        if not parent_user_directory:
            parent_owner = frappe.db.get_value(
                'Drive Entity', new_parent, 'owner') if new_parent else frappe.session.user
            try:
                parent_user_directory = get_user_directory(parent_owner)
            except FileNotFoundError:
                parent_user_directory = create_user_directory()
            new_parent = new_parent or parent_user_directory.name
            parent_is_group = frappe.db.get_value(
                'Drive Entity', new_parent, 'is_group')
            if not parent_is_group:
                raise NotADirectoryError()
            if not frappe.has_permission(doctype='Drive Entity', doc=new_parent, ptype='write', user=frappe.session.user):
                frappe.throw(
                    'Cannot paste to this folder due to insufficient permissions', frappe.PermissionError)
            if self.name == new_parent or self.name in get_ancestors_of('Drive Entity', new_parent):
                frappe.throw('You cannot copy a folder into itself')

        name = uuid.uuid4().hex

        if self.is_group:
            drive_entity = frappe.get_doc({
                'doctype': 'Drive Entity',
                'name': name,
                'title': self.title,
                'is_group': 1,
                'parent_drive_entity': new_parent,
                'color': self.color,
            })
            drive_entity.insert()

            for child in self.get_children():
                child.copy(name, parent_user_directory)

        else:
            save_path = Path(parent_user_directory.path) / \
                f'{new_parent}_{self.title}'
            if save_path.exists():
                frappe.throw(
                    f"File '{self.title}' already exists", FileExistsError)

            shutil.copy(self.path, save_path)

            path = save_path.parent / f'{name}{save_path.suffix}'
            save_path.rename(path)
            drive_entity = frappe.get_doc({
                'doctype': 'Drive Entity',
                'name': name,
                'title': self.title,
                'parent_drive_entity': new_parent,
                'path': path,
                'file_size': self.file_size,
                'file_ext': self.file_ext,
                'mime_type': self.mime_type
            })
            drive_entity.flags.file_created = True
            frappe.local.rollback_observers.append(drive_entity)
            drive_entity.insert()

        if new_parent == parent_user_directory.name:
            drive_entity.share(frappe.session.user, write=1, share=1)

    @frappe.whitelist()
    def rename(self, new_title):
        """
        Rename file or folder

        :param new_title: New file or folder name
        :raises FileExistsError: If a file or folder with the same name already exists in the parent folder
        :return: DriveEntity doc once it's renamed
        """

        self.title = new_title
        self.save()
        return self

    @frappe.whitelist()
    def change_color(self, new_color):
        """
        Change color of a folder

        :param new_color: New color selected for folder
        :raises InvalidColor: If the color is not a hex value string
        :return: DriveEntity doc once it's updated
        """

        self.color = new_color
        self.save()
        return self

    @frappe.whitelist()
    def set_general_access(self, new_access):
        """
        Set general sharing access for entity

        :param new_access: Dict with new read and write value
        """

        if new_access['read']:
            flags = {
                "ignore_share_permission": True} if frappe.session.user == self.owner else None
            frappe.share.add_docshare(
                'Drive Entity', self.name, write=new_access['write'], share=0, everyone=1, flags=flags)

        else:
            flags = {
                "ignore_permissions": True} if frappe.session.user == self.owner else None
            if frappe.db.exists({
                    'doctype': 'DocShare',
                    'share_doctype': 'Drive Entity',
                    'share_name': self.name,
                    'everyone': 1
            }):
                frappe.share.remove(
                    'Drive Entity', self.name, user=None, flags=flags)

        self.save()
        if self.is_group:
            for child in self.get_children():
                child.set_general_access(new_access)

    @frappe.whitelist()
    def toggle_allow_comments(self):
        """
        Toggle allow comments for entity

        """

        self.allow_comments = not self.allow_comments
        self.save()
        if self.is_group:
            for child in self.get_children():
                child.toggle_allow_comments()

    @frappe.whitelist()
    def toggle_allow_download(self):
        """
        Toggle allow download for entity

        """

        self.allow_download = not self.allow_download
        self.save()
        if self.is_group:
            for child in self.get_children():
                child.toggle_allow_download()

    @frappe.whitelist()
    def share(self, user, write=0, share=1, notify=1):
        """
        Share this file or folder with the specified user.
        If it has already been shared, update permissions.

        :param user: User with whom this is to be shared
        :param write: 1 if write permission is to be granted. Defaults to 0
        :param share: 1 if share permission is to be granted. Defaults to 0
        :param notify: 1 if the user should be notified. Defaults to 1
        """

        flags = {
            "ignore_share_permission": True} if frappe.session.user == self.owner else None
        if self.is_group:
            for child in self.get_children():
                child.share(user, write, share, 0)
            frappe.share.add_docshare(
                'Drive Entity', self.name, user, write=write, share=share, notify=notify, flags=flags)
        else:
            frappe.share.add_docshare(
                'Drive Entity', self.name, user, write=write, share=share, notify=notify, flags=flags)

    @frappe.whitelist()
    def unshare(self, user):
        """Unshare this file or folder with the specified user

        :param user: User with whom this is to be shared
        """

        if frappe.has_permission(doctype='Drive Entity', doc=self.name, ptype='share', user=frappe.session.user) or frappe.session.user == self.owner:
            flags = {"ignore_permissions": True}
        if self.is_group:
            for child in self.get_children():
                child.unshare(user)
            frappe.share.remove('Drive Entity', self.name, user, flags=flags)
        else:
            frappe.share.remove('Drive Entity', self.name, user, flags=flags)
