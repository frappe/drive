import frappe
from frappe.model.document import Document
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
from drive.api.format import mime_to_human
from drive.api.files import get_ancestors_of
from drive.api.files import generate_upward_path


class DriveEntity(Document):
    def before_save(self):
        self.version = self.version + 1
        self.file_kind = mime_to_human(self.mime_type, self.is_group)

    def after_insert(self):
        self.inherit_permissions()

    def on_trash(self):
        frappe.db.delete("Drive Favourite", {"entity": self.name})
        frappe.db.delete("Drive Entity Log", {"entity_name": self.name})
        frappe.db.delete("Drive DocShare", {"share_name": self.name})
        if self.is_group or self.document:
            for child in self.get_children():
                has_write_access = frappe.has_permission(
                    doctype="Drive Entity",
                    doc=self,
                    ptype="write",
                    user=frappe.session.user,
                )
                child.delete(ignore_permissions=has_write_access)

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

    def inherit_permissions(self):
        """Cascade parent permissions to new child entity"""

        if self.parent_drive_entity is None:
            return

        permissions = frappe.get_all(
            "Drive DocShare",
            fields=[
                "name",
                "user_doctype",
                "user_name",
                "read",
                "write",
                "share",
                "everyone",
                "public",
                "owner",
                "creation",
            ],
            filters=dict(share_doctype=self.doctype, share_name=self.parent_drive_entity),
        )

        parent_folder = frappe.db.get_value(
            "Drive Entity",
            self.parent_drive_entity,
            ["name", "owner", "allow_comments", "allow_download"],
            as_dict=1,
        )

        if parent_folder.owner != frappe.session.user:
            # Allow the owner of the folder to access the entity
            # Defaults to write since its obvious that the current user has write access to the parent
            # the subsequent for loop still creates a docShare for this uploaded entity as a side effect
            # It just lingers around and is wiped on delete (find a way to avoid the side effect if possible)
            self.share(
                share_name=self.name,
                user=parent_folder.owner,
                user_type="User",
                read=1,
                write=1,
                share=1,
                notify=0,
            )

        for permission in permissions:
            self.share(
                share_name=self.name,
                user=permission.user_name,
                user_type=permission.user_doctype,
                read=permission.read,
                write=permission.write,
                share=permission.share,
                everyone=permission.everyone,
                public=permission.public,
                notify=0,
            )
        self.allow_comments = parent_folder.allow_comments
        self.allow_download = parent_folder.allow_download
        self.save()

    def get_children(self):
        """Return a generator that yields child Documents."""
        child_names = frappe.get_list(
            self.doctype, filters={"parent_drive_entity": self.name}, pluck="name"
        )
        for name in child_names:
            yield frappe.get_doc(self.doctype, name)

    @frappe.whitelist()
    def move(self, new_parent=None):
        """
        Move file or folder to the new parent folder

        :param new_parent: Document-name of the new parent folder. Defaults to the user directory
        :raises NotADirectoryError: If the new_parent is not a folder, or does not exist
        :raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
        :return: DriveEntity doc once file is moved
        """

        new_parent = new_parent or get_user_directory(self.owner).name
        if new_parent == self.parent_drive_entity:
            return self

        is_group = frappe.db.get_value("Drive Entity", new_parent, "is_group")
        if not is_group:
            raise NotADirectoryError()
        for child in self.get_children():
            if child.name == self.name or new_parent:
                frappe.throw(
                    "Cannot move into itself",
                    frappe.PermissionError,
                )
                return
        self.parent_drive_entity = new_parent
        title = get_new_title(self.title, new_parent)
        if title != self.title:
            self.rename(title)
        self.inherit_permissions()
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

    @frappe.whitelist(allow_guest=True)
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
                "mime_type": self.mime_type,
                "is_group": self.is_group,
            }
        )
        if entity_exists:
            suggested_name = get_new_title(
                new_title, self.parent_drive_entity, document=self.document, folder=self.is_group
            )
            frappe.throw(
                f"{'Folder' if self.is_group else 'File'} '{new_title}' already exists\n Try '{suggested_name}' ",
                FileExistsError,
            )
            return suggested_name

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
        return frappe.db.set_value(
            "Drive Entity", self.name, "color", new_color, update_modified=False
        )

    @frappe.whitelist()
    def set_general_access(self, read, write, everyone, public, share, share_name=None):
        """
        Set general sharing access for entity

        :param new_access: Dict with new read and write value
        """

        if read:
            if frappe.session.user == self.owner:
                self.share(
                    share_name=share_name,
                    read=read,
                    write=write,
                    share=0,
                    everyone=everyone,
                    public=public,
                )

        else:
            flags = {"ignore_permissions": True} if frappe.session.user == self.owner else None
            self.unshare(user=None, user_type=None)

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
        share_name=None,
        user=None,
        user_type=None,
        read=1,
        write=0,
        share=0,
        everyone=0,
        public=0,
        notify=0,
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

        if frappe.session.user != self.owner:
            if not frappe.has_permission(
                doctype="Drive Entity",
                doc=self,
                ptype="share",
                user=frappe.session.user,
            ):
                for owner in get_ancestors_of(self.name):
                    if frappe.session.user == frappe.get_value(
                        "Drive Entity", {"name": owner}, ["owner"]
                    ):
                        continue
                    else:
                        frappe.throw("Not permitted to share", frappe.PermissionError)
                        break
        if user:
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "user_name": user,
                    "user_doctype": user_type,
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                },
            )
        if cint(public) or cint(everyone):
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                    "user_name": None,
                    "user_doctype": None,
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

        doc.update(
            {
                # always add read, since you are adding!
                "read": 1,
                "write": cint(write),
                "share": cint(share),
                "everyone": cint(everyone),
                "public": cint(public),
            }
        )

        if frappe.db.exists(
            {
                "doctype": "Drive DocShare",
                "share_doctype": "Drive Entity",
                "share_name": self.parent_drive_entity,
                "everyone": cint(everyone),
                "public": cint(public),
                "user_name": user,
                "user_doctype": user_type,
            }
        ):
            parent_docshare = frappe.db.get_value(
                "Drive DocShare",
                {
                    "share_doctype": "Drive Entity",
                    "share_name": self.parent_drive_entity,
                    "everyone": cint(everyone),
                    "public": cint(public),
                    "user_name": user,
                    "user_doctype": user_type,
                },
                "name",
            )
            doc.update({"owner_parent": parent_docshare, "share_parent": parent_docshare})
        doc.save(ignore_permissions=True)
        if self.is_group:
            for child in self.get_children():
                child.share(
                    user=user,
                    user_type=user_type,
                    read=read,
                    write=write,
                    share=share,
                    everyone=everyone,
                    public=public,
                )

    @frappe.whitelist()
    def unshare(self, user, user_type="User"):
        """Unshare this file or folder with the specified user

        :param user: User or group with whom this is to be shared
        :param user_type:
        """

        if user:
            if user != self.owner and frappe.session.user != self.owner:
                shared_parent = frappe.db.exists(
                    "Drive DocShare",
                    {
                        "user_name": user,
                        "user_doctype": user_type,
                        "share_name": self.parent_drive_entity,
                        "share_doctype": "Drive Entity",
                    },
                )
                if shared_parent:
                    return

            absolute_path = generate_upward_path(self.name)
            for i in absolute_path:
                if i.owner == user:
                    frappe.throw("User owns parent folder", frappe.PermissionError)

            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "user_name": user,
                    "user_doctype": user_type,
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                },
            )
        else:
            share_name = frappe.db.get_value(
                "Drive DocShare",
                {
                    "share_name": self.name,
                    "share_doctype": "Drive Entity",
                    "user_name": None,
                    "user_doctype": None,
                },
            )

        if share_name:
            if frappe.session.user == user or frappe.session.user == self.owner:
                frappe.db.delete("Drive DocShare", share_name)
            else:
                frappe.delete_doc("Drive DocShare", share_name, ignore_permissions=True)
        if self.is_group:
            for child in self.get_children():
                child.unshare(user, user_type)

def on_doctype_update():
    frappe.db.add_index("Drive Entity", ["title"])

