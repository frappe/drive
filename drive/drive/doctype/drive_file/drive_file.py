import shutil
from pathlib import Path

import frappe
from frappe.model.document import Document
from frappe.utils import now

from drive.api.activity import create_new_activity_log
from drive.api.files import get_new_title
from drive.api.permissions import get_user_access, user_has_permission
from drive.utils import generate_upward_path, get_ancestors_of, get_home_folder, update_file_size
from drive.utils.files import FileManager


class DriveFile(Document):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def manager(self):
        return FileManager()

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
                has_write_access = user_has_permission(self, "write")
                child.delete(ignore_permissions=has_write_access)

    def after_delete(self):
        """Cleanup after entity is deleted"""
        if self.document:
            frappe.delete_doc("Drive Document", self.document)

        if self.path:
            self.manager.delete_file(self.team, self.name, self.path)

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

    def __update_modified(func):
        def decorator(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            frappe.db.set_value("Drive File", self.name, "_modified", now())
            return res

        return decorator

    @__update_modified
    def move(self, new_parent=None, new_team=None):
        """
        Move file or folder to the new parent folder
        If not owned by current user, copies it.

        :param new_parent: Document-name of the new parent folder. Defaults to the user directory
        :raises NotADirectoryError: If the new_parent is not a folder, or does not exist
        :raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
        :return: DriveEntity doc once file is moved
        """
        new_team = new_team or self.team
        new_parent = new_parent or get_home_folder(new_team).name

        if new_parent == self.parent_entity:
            return

        if new_parent == self.name:
            frappe.throw(
                "Cannot move into itself",
                frappe.PermissionError,
            )
        if not frappe.db.get_value("Drive File", new_parent, "is_group"):
            frappe.throw(
                "Can only move into folders",
                NotADirectoryError,
            )

        for child in self.get_children():
            if child.name == self.name or child.name == new_parent:
                frappe.throw(
                    "Cannot move into itself",
                    frappe.PermissionError,
                )
                return frappe.get_value(
                    "Drive File",
                    self.parent_entity,
                    ["title", "team", "name"],
                    as_dict=True,
                )
            else:
                child.move(self.name, new_team)

        if new_parent != self.parent_entity:
            update_file_size(self.parent_entity, -self.file_size)
            update_file_size(new_parent, +self.file_size)
            self.parent_entity = new_parent

        self.title = get_new_title(self.title, new_parent, self.is_group, self.name)
        self.team = new_team

        not_in_disk = self.document or self.mime_type == "frappe/slides" or self.is_link

        # Condition is so that old file names aren't corrupted
        if not self.manager.flat and not not_in_disk:
            new_path = self.manager.get_disk_path(self)
            self.manager.move(self.path, str(new_path))
            self.path = new_path

        self.save()

        return frappe.get_value(
            "Drive File", new_parent, ["title", "team", "name", "parent_entity"], as_dict=True
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
            if not user_has_permission(new_parent, "upload"):
                frappe.throw(
                    "Cannot paste to this folder due to insufficient permissions",
                    frappe.PermissionError,
                )
            if self.name == new_parent or self.name in get_ancestors_of("Drive File", new_parent):
                frappe.throw("You cannot copy a folder into itself")

            title = get_new_title(title, new_parent, self.name)

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
    @__update_modified
    def rename(self, new_title):
        """
        Rename file or folder

        :param new_title: New file or folder name
        :raises FileExistsError: If a file or folder with the same name already exists in the parent folder
        :return: DriveEntity doc once it's renamed
        """
        if new_title == self.title:
            return self

        validated_name = get_new_title(new_title, self.parent_entity, self.is_group, self.name)
        if new_title != validated_name and new_title != "Untitled Document":
            return frappe.throw(
                f"{'Folder' if self.is_group else 'File'} '{new_title}' already exists\n Try '{validated_name}' ",
                FileExistsError,
            )

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
        path = self.manager.rename(self)
        if path:
            self.path = path
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

    def permanent_delete(self):
        write_access = user_has_permission(self, "write")
        parent_write_access = user_has_permission(self.parent_entity, "write")

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
        team=False,
    ):
        if frappe.session.user != self.owner and not user_has_permission(self, "share"):
            # Complicated logic was removed here
            frappe.throw("Not permitted to share", frappe.PermissionError)

        # Clean out existing general records
        if not user or team:
            self.unshare("$GENERAL")

        permission = frappe.db.get_value(
            "Drive Permission",
            {
                "entity": self.name,
                "user": user or "",
                "team": team,
            },
        )
        if not permission:
            permission = frappe.new_doc("Drive Permission")
            permission.update(
                {
                    "user": user,
                    "team": team,
                    "entity": self.name,
                }
            )
        else:
            permission = frappe.get_doc("Drive Permission", permission)

        levels = [
            ["read", read],
            ["comment", comment],
            ["share", share],
            ["upload", upload],
            ["write", write],
        ]
        permission.update({l[0]: l[1] for l in levels if l[1] is not None})

        permission.save(ignore_permissions=True)

    @frappe.whitelist()
    def unshare(self, user=None):
        """Unshare this file or folder with the specified user
        :param user: User or group with whom this is to be shared
        :param user_type:
        """
        absolute_path = generate_upward_path(self.name)
        for i in absolute_path:
            if i["owner"] == user:
                frappe.throw("User owns parent folder", frappe.PermissionError)

        if user == "$GENERAL":
            perm_names = frappe.db.get_list(
                "Drive Permission",
                {"entity": self.name},
                or_filters={"user": "", "team": 1},
                pluck="name",
            )
            for perm_name in perm_names:
                frappe.delete_doc("Drive Permission", perm_name, ignore_permissions=True)

            # If overriding perms of a parent folder, write out an explicit denial
            public_access = get_user_access(self, "Guest")
            team_access = get_user_access(self, team=1)
            user = None
            if public_access["read"]:
                user = ""
            elif team_access["read"]:
                user = team_access["team"]

            # Doesn't work as higher access "overrides" in get_user_access
            if user is not None:
                frappe.get_doc(
                    {
                        "doctype": "Drive Permission",
                        "user": user,
                        "entity": self.name,
                        "read": 0,
                        "comment": 0,
                        "share": 0,
                        "write": 0,
                        "team": bool(user),
                    }
                ).insert()

        else:
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
