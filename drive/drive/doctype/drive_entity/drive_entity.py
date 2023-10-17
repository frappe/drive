import frappe
from frappe.utils.nestedset import NestedSet, get_ancestors_of
from pathlib import Path
import shutil
import uuid
from drive.utils.files import (
    get_user_directory,
    create_user_directory,
    get_new_title,
    get_user_thumbnails_directory,
    create_user_thumbnails_directory,
    create_thumbnail,
)
from drive.utils.user_group import add_new_user_group_docshare, does_exist_user_group_docshare
from frappe.utils import cint


class DriveEntity(NestedSet):
    nsm_parent_field = "parent_drive_entity"
    nsm_oldparent_field = "old_parent"

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
            frappe.share.add_docshare(
                "Drive Entity",
                self.name,
                permission.user,
                write=permission.write,
                share=permission.share,
                everyone=permission.everyone,
                notify=0,
                flags={"ignore_share_permission": True},
            )

    def on_trash(self):
        frappe.db.delete("Drive Favourite", {"entity": self.name})
        if self.is_group:
            for child in self.get_children():
                has_write_access = frappe.has_permission(
                    doctype="Drive Entity",
                    doc=self,
                    ptype="write",
                    user=frappe.session.user,
                )
                child.delete(ignore_permissions=has_write_access)
            super().on_trash()

    def after_delete(self):
        if self.document:
            frappe.delete_doc("Drive Document", self.document)
        """Remove file once document is deleted"""
        if self.path:
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    Path(self.path).unlink()
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Failed to delete file - {e}")
        if self.mime_type:
            if self.mime_type.startswith("image") or self.mime_type.startswith("video"):
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        user_thumbnails_directory = get_user_thumbnails_directory()
                        thumbnail_getpath = Path(user_thumbnails_directory, self.name)
                        Path(str(thumbnail_getpath) + ".thumbnail").unlink()
                        break
                    except Exception as e:
                        print(f"Attempt {attempt + 1}: Failed to delete thumbnail - {e}")

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
        if new_parent == self.parent_drive_entity:
            return self

        is_group = frappe.db.get_value("Drive Entity", new_parent, "is_group")
        if not is_group:
            raise NotADirectoryError()
        self.parent_drive_entity = new_parent
        title = get_new_title(self.title, new_parent)
        if title != self.title:
            self.rename(title)
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

        title = self.title

        if not parent_user_directory:
            parent_owner = (
                frappe.db.get_value("Drive Entity", new_parent, "owner")
                if new_parent
                else frappe.session.user
            )
            try:
                parent_user_directory = get_user_directory(parent_owner)
            except FileNotFoundError:
                parent_user_directory = create_user_directory()
            new_parent = new_parent or parent_user_directory.name
            parent_is_group = frappe.db.get_value("Drive Entity", new_parent, "is_group")
            if not parent_is_group:
                raise NotADirectoryError()
            if not frappe.has_permission(
                doctype="Drive Entity",
                doc=new_parent,
                ptype="write",
                user=frappe.session.user,
            ):
                frappe.throw(
                    "Cannot paste to this folder due to insufficient permissions",
                    frappe.PermissionError,
                )
            if self.name == new_parent or self.name in get_ancestors_of(
                "Drive Entity", new_parent
            ):
                frappe.throw("You cannot copy a folder into itself")

            title = get_new_title(title, new_parent)

        name = uuid.uuid4().hex

        if self.is_group:
            drive_entity = frappe.get_doc(
                {
                    "doctype": "Drive Entity",
                    "name": name,
                    "title": title,
                    "is_group": 1,
                    "parent_drive_entity": new_parent,
                    "color": self.color,
                }
            )
            drive_entity.insert()

            for child in self.get_children():
                child.copy(name, parent_user_directory)

        elif self.document is not None:
            drive_doc_content = frappe.db.get_value("Drive Document", self.document, "content")

            new_drive_doc = frappe.new_doc("Drive Document")
            new_drive_doc.title = title
            new_drive_doc.content = drive_doc_content
            new_drive_doc.save()

            drive_entity = frappe.get_doc(
                {
                    "doctype": "Drive Entity",
                    "name": name,
                    "title": title,
                    "mime_type": self.mime_type,
                    "parent_drive_entity": new_parent,
                    "document": new_drive_doc,
                }
            )
            drive_entity.insert()

        else:
            save_path = Path(parent_user_directory.path) / f"{new_parent}_{title}"
            if save_path.exists():
                frappe.throw(f"File '{title}' already exists", FileExistsError)

            shutil.copy(self.path, save_path)

            path = save_path.parent / f"{name}{save_path.suffix}"
            save_path.rename(path)
            drive_entity = frappe.get_doc(
                {
                    "doctype": "Drive Entity",
                    "name": name,
                    "title": title,
                    "parent_drive_entity": new_parent,
                    "path": path,
                    "file_size": self.file_size,
                    "file_ext": self.file_ext,
                    "mime_type": self.mime_type,
                }
            )
            drive_entity.flags.file_created = True
            drive_entity.insert()

        if new_parent == parent_user_directory.name:
            drive_entity.share(frappe.session.user, write=1, share=1)

        if drive_entity.mime_type:
            if drive_entity.mime_type.startswith("image") or drive_entity.mime_type.startswith(
                "video"
            ):
                frappe.enqueue(
                    create_thumbnail,
                    queue="default",
                    timeout=None,
                    now=True,
                    # will set to false once reactivity in new UI is solved
                    entity_name=name,
                    path=path,
                    mime_type=drive_entity.mime_type,
                )

    @frappe.whitelist()
    def rename(self, new_title):
        """
        Rename file or folder

        :param new_title: New file or folder name
        :raises FileExistsError: If a file or folder with the same name already exists in the parent folder
        :return: DriveEntity doc once it's renamed
        """

        if new_title == self.title:
            return self

        entity_exists = frappe.db.exists(
            {
                "doctype": "Drive Entity",
                "parent_drive_entity": self.parent_drive_entity,
                "title": new_title,
            }
        )
        if entity_exists:
            frappe.throw(
                f"{'Folder' if self.is_group else 'File'} '{new_title}' already exists",
                FileExistsError,
            )

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

        if new_access["read"]:
            flags = (
                {"ignore_share_permission": True} if frappe.session.user == self.owner else None
            )
            self.share(
                user=None,
                user_type=None,
                read=new_access["read"],
                write=new_access["write"],
                share=0,
                public=1,
            )

        else:
            flags = {"ignore_permissions": True} if frappe.session.user == self.owner else None
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                    "public": 1,
                },
            )
            if share_name:
                frappe.delete_doc("Drive DocShare", share_name, flags=flags)

        self.save()
        if self.is_group:
            for child in self.get_children():
                child.set_general_access(
                    user=None,
                    user_type=None,
                    read=new_access["read"],
                    write=new_access["write"],
                    share=0,
                )

    @frappe.whitelist()
    def toggle_allow_comments(self, new_value):
        """
        Toggle allow comments for entity

        """

        self.db_set("allow_comments", new_value, commit=True, update_modified=False)
        if self.is_group:
            for child in self.get_children():
                child.toggle_allow_comments(new_value)

    @frappe.whitelist()
    def toggle_allow_download(self, new_value):
        """
        Toggle allow download for entity

        """
        self.db_set("allow_download", new_value, commit=True, update_modified=False)
        if self.is_group:
            for child in self.get_children():
                child.toggle_allow_download(new_value)

    @frappe.whitelist()
    def share(
        self,
        user,
        user_type="User",
        read=1,
        write=0,
        share=0,
        everyone=0,
        public=0,
        notify=0,
        is_user_group=None,
    ):
        """
        Share this file or folder with the specified user.
        If it has already been shared, update permissions.
        Share defaults to one to let the non owner user unshare a file.

        :param user: User with whom this is to be shared
        :param write: 1 if write permission is to be granted. Defaults to 0
        :param share: 1 if share permission is to be granted. Defaults to 0
        :param notify: 1 if the user should be notified. Defaults to 1
        """
        flags = {"ignore_share_permission": True} if frappe.session.user == self.owner else None
        if cint(everyone):
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "everyone": 1,
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                },
            )
        if cint(public):
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "public": 1,
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                },
            )
        else:
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "user_name": user,
                    "user_doctype": user_type,
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                },
            )

        if share_name:
            doc = frappe.get_doc("Drive DocShare", share_name)
        else:
            doc = frappe.new_doc("Drive DocShare")
            doc.update(
                {
                    "user_name": user,
                    "user_doctype": user_type,
                    "share_doctype": "Drive Entity",
                    "share_name": self.name,
                    "everyone": cint(everyone),
                    "public": cint(public),
                }
            )

        if flags:
            doc.flags.update(flags)

        doc.update(
            {
                # always add read, since you are adding!
                "read": 1,
                "write": cint(write),
                "share": cint(share),
            }
        )

        if self.is_group:
            for child in self.get_children():
                child.share(user, user_type, write, share, everyone, public)

        doc.save(ignore_permissions=True)

    @frappe.whitelist()
    def unshare(self, user, user_type="User"):
        """Unshare this file or folder with the specified user

        :param user: User or group with whom this is to be shared
        :param user_type:
        """

        if (
            frappe.has_permission(
                doctype="Drive Entity",
                doc=self.name,
                ptype="read",
                user=frappe.session.user,
            )
            or frappe.session.user == self.owner
        ):
            flags = {"ignore_permissions": True}

        share_name = frappe.db.get_value(
            "Drive DocShare",
            {
                "user_name": user,
                "user_doctype": user_type,
                "share_name": self.name,
                "share_doctype": "Drive Entity",
            },
        )

        if share_name:
            frappe.delete_doc("Drive DocShare", share_name, flags=flags)

        if self.is_group:
            for child in self.get_children():
                child.unshare(user, user_type)

        if user_type == "User":
            recent_name = frappe.db.get_value(
                "Drive Entity Log",
                {
                    "user": user,
                    "entity_name": self.name,
                },
            )
            if recent_name:
                frappe.delete_doc("Drive Entity Log", recent_name, flags=flags)

            favourite_name = frappe.db.get_value(
                "Drive Favourite",
                {
                    "user": user,
                    "entity": self.name,
                },
            )
            if favourite_name:
                frappe.delete_doc("Drive Favourite", favourite_name, flags=flags)
