import frappe
from frappe.model.document import Document
from pathlib import Path
import shutil
from drive.utils.files import (
    get_home_folder,
    get_new_title,
    get_team_thumbnails_directory,
    update_file_size,
    FileManager,
)
from drive.api.files import get_ancestors_of
from drive.utils.files import generate_upward_path
from drive.api.activity import create_new_activity_log


class DriveFile(Document):
    def after_insert(self):
        full_name = frappe.db.get_value("User", {"name": frappe.session.user}, ["full_name"])
        message = f"{full_name} created {self.title}"
        create_new_activity_log(
            entity=self.name,
            activity_type="create",
            activity_message=message,
            document_field="title",
            field_new_value=self.title,
        )

    def on_trash(self):
        frappe.db.delete("Drive Favourite", {"entity": self.name})
        frappe.db.delete("Drive Entity Log", {"entity_name": self.name})
        frappe.db.delete("Drive Permission", {"entity": self.name})
        frappe.db.delete("Drive Notification", {"notif_doctype_name": self.name})
        frappe.db.delete("Drive Entity Activity Log", {"entity": self.name})

        if self.is_group or self.document:
            for child in self.get_children():
                has_write_access = frappe.has_permission(
                    doctype="Drive File",
                    doc=self,
                    ptype="write",
                    user=frappe.session.user,
                )
                child.delete(ignore_permissions=has_write_access)

    def after_delete(self):
        """Cleanup after entity is deleted"""
        if self.document:
            frappe.delete_doc("Drive Document", self.document)

        if self.path:
            manager = FileManager()
            manager.delete_file(self.team, self.name, self.path)

    def on_rollback(self):
        if self.flags.file_created:
            shutil.rmtree(self.path) if self.is_group else self.path.unlink()

    def get_children(self):
        """Return a generator that yields child Documents."""
        child_names = frappe.get_list(
            self.doctype, filters={"parent_entity": self.name}, pluck="name"
        )
        for name in child_names:
            yield frappe.get_doc(self.doctype, name)

    def move(self, new_parent=None, is_private=None):
        """
        Move file or folder to the new parent folder
        If not owned by current user, copies it.

        :param new_parent: Document-name of the new parent folder. Defaults to the user directory
        :raises NotADirectoryError: If the new_parent is not a folder, or does not exist
        :raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
        :return: DriveEntity doc once file is moved
        """
        new_parent = new_parent or get_home_folder(self.team).name
        if new_parent == self.parent_entity:
            if is_private is not None:
                self.is_private = int(is_private)
                self.save()
            return frappe.get_value(
                "Drive File",
                self.parent_entity,
                ["title", "team", "name", "is_private"],
                as_dict=True,
            )

        if new_parent == self.name:
            frappe.throw(
                "Cannot move into itself",
                frappe.PermissionError,
            )

        is_group = frappe.db.get_value("Drive File", new_parent, "is_group")
        if not is_group:
            raise NotADirectoryError()

        for child in self.get_children():
            if child.name == self.name or child.name == new_parent:
                frappe.throw(
                    "Cannot move into itself",
                    frappe.PermissionError,
                )
                return frappe.get_value(
                    "Drive File",
                    self.parent_entity,
                    ["title", "team", "name", "is_private"],
                    as_dict=True,
                )

        update_file_size(self.parent_entity, -self.file_size)
        update_file_size(new_parent, +self.file_size)

        self.parent_entity = new_parent
        self.is_private = frappe.db.get_value("Drive File", new_parent, "is_private")

        title = get_new_title(self.title, new_parent)
        if title != self.title:
            self.rename(title)
        self.save()

        return frappe.get_value(
            "Drive File", new_parent, ["title", "team", "name", "is_private"], as_dict=True
        )

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
                frappe.db.get_value("Drive File", new_parent, "owner")
                if new_parent
                else frappe.session.user
            )
            # BROKEN - parent dir is team
            new_parent = new_parent or parent_user_directory.name
            parent_is_group = frappe.db.get_value("Drive File", new_parent, "is_group")
            if not parent_is_group:
                raise NotADirectoryError()
            if not frappe.has_permission(
                doctype="Drive File",
                doc=new_parent,
                ptype="write",
                user=frappe.session.user,
            ):
                frappe.throw(
                    "Cannot paste to this folder due to insufficient permissions",
                    frappe.PermissionError,
                )
            if self.name == new_parent or self.name in get_ancestors_of("Drive File", new_parent):
                frappe.throw("You cannot copy a folder into itself")

            title = get_new_title(title, new_parent)

        if self.is_group:
            drive_entity = frappe.get_doc(
                {
                    "doctype": "Drive File",
                    "name": name,
                    "title": title,
                    "is_group": 1,
                    "parent_entity": new_parent,
                    "color": self.color,
                }
            )
            drive_entity.insert()

            for child in self.get_children():
                child.copy(name, parent_user_directory)

        elif self.document is not None:
            drive_doc_content = frappe.db.get_list("Drive Document", self.document, "content")

            new_drive_doc = frappe.new_doc("Drive Document")
            new_drive_doc.title = title
            new_drive_doc.content = drive_doc_content
            new_drive_doc.save()

            drive_entity = frappe.get_doc(
                {
                    "doctype": "Drive File",
                    "name": name,
                    "title": title,
                    "mime_type": self.mime_type,
                    "parent_entity": new_parent,
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
                    "doctype": "Drive File",
                    "name": name,
                    "title": title,
                    "parent_entity": new_parent,
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
                "doctype": "Drive File",
                "parent_entity": self.parent_entity,
                "title": new_title,
                "mime_type": self.mime_type,
                "is_group": self.is_group,
            }
        )

        # Only exception
        if entity_exists and new_title != "Untitled Document":
            suggested_name = get_new_title(new_title, self.parent_entity, folder=self.is_group)
            frappe.throw(
                f"{'Folder' if self.is_group else 'File'} '{new_title}' already exists\n Try '{suggested_name}' ",
                FileExistsError,
            )
            return suggested_name
        full_name = frappe.db.get_value("User", {"name": frappe.session.user}, ["full_name"])
        message = f"{full_name} renamed {self.title} to {new_title}"
        create_new_activity_log(
            entity=self.name,
            activity_type="rename",
            activity_message=message,
            document_field="title",
            field_old_value=self.title,
            field_new_value=new_title,
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
        return frappe.db.set_value(
            "Drive File", self.name, "color", new_color, update_modified=False
        )

    @frappe.whitelist()
    def toggle_personal(self, new_value, move_root=True):
        """
        Toggle is private for file
        """
        # BROKEN: don't allow personal unless whole breadcrumb is personal
        self.is_private = new_value
        if not new_value and move_root:
            self.move()
        if self.is_group:
            for child in self.get_children():
                child.toggle_personal(new_value, False)
        self.save()
        return self.name

    def permanent_delete(self):
        write_access = frappe.has_permission(doctype="Drive File", doc=self, ptype="write")
        parent_write_access = frappe.has_permission(
            doctype="Drive File",
            doc=frappe.get_value("Drive File", self, "parent_entity"),
            ptype="write",
        )

        if not (write_access or parent_write_access):
            frappe.throw("Not permitted", frappe.PermissionError)

        self.is_active = -1
        if self.is_group:
            for child in self.get_children():
                child.permanent_delete()
        self.save()

    @frappe.whitelist()
    def share(
        self,
        user=None,
        read=None,
        comment=None,
        share=None,
        upload=None,
        write=None,
        valid_until="",
    ):
        """
        Share this file or folder with the specified user.
        If it has already been shared, update permissions.
        Share defaults to one to let the non owner user unshare a file.

        :param user: User with whom this is to be shared
        :param write: 1 if write permission is to be granted. Defaults to 0
        :param share: 1 if share permission is to be granted. Defaults to 0
        """
        if frappe.session.user != self.owner:
            if not frappe.has_permission(
                doctype="Drive File",
                doc=self,
                ptype="share",
                user=frappe.session.user,
            ):
                for owner in get_ancestors_of(self.name):
                    if frappe.session.user == frappe.get_value(
                        "Drive File", {"name": owner}, ["owner"]
                    ):
                        continue
                    else:
                        frappe.throw("Not permitted to share", frappe.PermissionError)
                        break

        permission = frappe.db.get_value(
            "Drive Permission",
            {
                "entity": self.name,
                "user": user or "",
            },
        )
        if not permission:
            permission = frappe.new_doc("Drive Permission")
        else:
            permission = frappe.get_doc("Drive Permission", permission)

        levels = [
            ["read", read],
            ["comment", comment],
            ["share", share],
            ["upload", upload],
            ["write", write],
        ]
        permission.update(
            {
                "user": user,
                "entity": self.name,
                "valid_until": valid_until,
            }
            | {l[0]: l[1] for l in levels if l[1] is not None}
        )

        permission.save(ignore_permissions=True)

    @frappe.whitelist()
    def unshare(self, user=None):
        """Unshare this file or folder with the specified user

        :param user: User or group with whom this is to be shared
        :param user_type:
        """
        absolute_path = generate_upward_path(self.name)
        for i in absolute_path:
            print(i)
            if i["owner"] == user:
                frappe.throw("User owns parent folder", frappe.PermissionError)

        perm_name = frappe.db.get_value(
            "Drive Permission",
            {
                "user": user,
                "entity": self.name,
            },
        )
        if perm_name:
            frappe.delete_doc("Drive Permission", perm_name, ignore_permissions=True)


def on_doctype_update():
    frappe.db.add_index("Drive File", ["title"])
