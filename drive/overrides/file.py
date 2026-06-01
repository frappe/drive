from pathlib import Path
import frappe
from frappe.core.doctype.file.file import File as FrappeFile
from frappe.core.doctype.file.utils import get_content_hash
from frappe.utils import get_files_path, now

from drive.api.files import get_file_type
from drive.api.permissions import get_user_access, user_has_permission
from drive.api.product import invite_users
from drive.api.activity import create_new_activity_log

from drive.utils import (
    generate_upward_path,
    get_home_folder,
    update_file_size,
    get_new_file_name,
    validate_filename,
    get_upload_path,
    STATUS_ACTIVE,
    STATUS_REMOVED,
)
from drive.utils.files import FileManager
import mimemapper


def only_for_drive_files(func):
    def inner(self, *args, **kwargs):
        if self.is_drive_file:
            return func(self, *args, **kwargs)
        else:
            parent_func = getattr(super(type(self), self), func.__name__, None)
            if not parent_func:
                raise ValueError("This function only exists for Drive files.")
            return parent_func(*args, **kwargs)

    return inner


class File(FrappeFile):
    @only_for_drive_files
    def validate(self):
        pass

    @only_for_drive_files
    def before_insert(self):
        pass

    @only_for_drive_files
    def generate_content_hash(self):
        pass

    @only_for_drive_files
    def get_full_path(self):
        return get_files_path(self.file_url, private=True)

    @only_for_drive_files
    def set_folder_name(self):
        pass

    @only_for_drive_files
    def autoname(self):
        if getattr(self, "_name", None):
            self.name = self._name
        else:
            self.name = frappe.generate_hash(length=10)

    @only_for_drive_files
    def set_is_private(self):
        self.is_private = 1

    @only_for_drive_files
    def set_file_type(self):
        pass

    # Drive methods
    def __update_modified(func):
        """Used for functions that meaningfuly "modify" a file"""

        def decorator(self, *args, **kwargs):
            # Legacy code
            res = func(self, *args, **kwargs)
            self.db_set("file_modified", now())
            return res

        return decorator

    @frappe.whitelist()
    def share(
        self,
        user: str = None,
        read: bool | None = None,
        comment: bool | None = None,
        share: bool | None = None,
        upload: bool | None = None,
        write: bool | None = None,
        team: bool = False,
    ):
        if not user_has_permission(self, "share"):
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

        # Create user
        if user and not frappe.db.exists("User", user):
            invite_users(user, auto=True)

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
    def unshare(self, user: str | None = None):
        if not user_has_permission(self, "share"):
            frappe.throw("Not permitted to unshare", frappe.PermissionError)

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

    @__update_modified
    def move(self, new_parent=None, new_team=None):
        """
        Move file to a new folder.
        """
        # Logic to decide new values
        if new_team and not new_parent:
            new_parent = new_parent or get_home_folder(new_team).name
        elif new_parent and not new_team:
            new_team = frappe.db.get_value("File", new_parent, "team")
        elif not new_parent and not new_team:
            new_team = self.team
            new_parent = new_parent or get_home_folder(new_team).name

        if new_parent == self.name:
            frappe.throw(
                "Cannot move into itself",
                ValueError,
            )
        elif not user_has_permission(new_parent, "upload") or not user_has_permission(self, "write"):
            frappe.throw("You don't have permission to move this file.", frappe.PermissionError)

        if not (
            frappe.db.get_value("File", new_parent, "is_folder")
            # FIX: disable after redesign
            or frappe.db.get_value("File", new_parent, "content_doctype")
        ):
            frappe.throw(
                "Can only move into folders",
                NotADirectoryError,
            )

        for child in self.get_children():
            if child.name == self.name or child.name == new_parent:
                frappe.throw(
                    "Cannot move into itself",
                    ValueError,
                )
            elif new_team != child.team:
                child.move(self.name, new_team)

        if new_parent != self.folder:
            update_file_size(self.folder, -self.file_size)
            update_file_size(new_parent, +self.file_size)
            self.folder = new_parent
            self.file_name = get_new_file_name(self.file_name, new_parent, self.is_folder, self.name)

        self.team = new_team
        not_in_disk = self.file_type == "Link" or not self.file_url

        # Update all the children's paths
        if not self.manager.flat and not not_in_disk:
            new_path = self.manager.get_disk_path(self)
            self.manager.move(self, str(new_path))
            self.recursive_path_move(self.file_url, new_path)
            self.file_url = new_path
        self.save()

        return frappe.get_value("File", new_parent, ["file_name", "team", "name", "folder"], as_dict=True)

    def toggle_favourite(self):
        existing_doc = frappe.db.exists(
            {
                "doctype": "Drive Favourite",
                "entity": self.name,
                "user": frappe.session.user,
            }
        )
        if existing_doc:
            frappe.delete_doc("Drive Favourite", existing_doc)
            return False
        else:
            frappe.get_doc(
                {
                    "doctype": "Drive Favourite",
                    "entity": self.name,
                    "user": frappe.session.user,
                }
            ).insert()
            return True

    @frappe.whitelist()
    @__update_modified
    def rename(self, new_file_name: str):
        """
        Rename file or folder
        """
        if not user_has_permission(self, "write"):
            frappe.throw("You cannot rename this file", frappe.PermissionError)

        if new_file_name == self.file_name:
            return self
        validate_filename(new_file_name, self.folder, self.file_type)

        full_name = frappe.db.get_value("User", {"name": frappe.session.user}, ["full_name"])
        message = f"{full_name} renamed {self.file_name} to {new_file_name}"
        create_new_activity_log(
            entity=self.name,
            activity_type="rename",
            activity_message=message,
            document_field="file_name",
            field_old_value=self.file_name,
            field_new_value=new_file_name,
        )
        if len(new_file_name) > 140:
            frappe.throw("Your file_name can't be more than 140 characters.")

        self.file_name = new_file_name
        path = self.manager.rename(self)
        if self.file_url and self.mime_type != "frappe/slides":
            self.recursive_path_move(self.file_url, path)

        self.save()

    def permanent_delete(self):
        write_access = user_has_permission(self, "write")
        parent_write_access = user_has_permission(self.folder, "write")
        if not (write_access or parent_write_access):
            frappe.throw("Not permitted", frappe.PermissionError)

        self.status = STATUS_REMOVED
        if self.is_folder:
            for child in self.get_children():
                child.permanent_delete()
        self.save()

    # Utils
    @property
    def manager(self):
        return FileManager()

    def recursive_path_move(self, old, new):
        if new:
            self.file_url = new
        for child in self.get_children():
            in_disk = child.file_type != "Link" and self.file_url
            if in_disk:
                child.recursive_path_move(child.file_url, str(Path(new) / Path(child.file_url).relative_to(old)))
        self.save()

    def get_children(self):
        """Returns a generator that yields child Documents."""
        child_names = frappe.get_list(self.doctype, filters={"folder": self.name}, pluck="name")
        for name in child_names:
            yield frappe.get_doc(self.doctype, name)


def after_upload_file(doc):
    if doc.is_drive_file:
        return
    settings = frappe.get_single("Drive Disk Settings")
    if frappe.form_dict.library_file_name:
        library_doc = frappe.get_doc("File", frappe.form_dict.library_file_name)
        doc.is_drive_file = library_doc.is_drive_file
        if doc.is_drive_file:
            doc.file_type = library_doc.file_type
            doc.file_size = library_doc.file_size
            doc.modified = library_doc.modified
            doc.content_doctype = "File"
            doc.content_docname = frappe.form_dict.library_file_name
    elif settings.use_drive_for_files and doc.attached_to_name:
        doc.is_drive_file = 1
        content_hash = get_content_hash(doc.content)
        temp_path = get_upload_path("private/files", content_hash[:6] + "-" + doc.file_name)
        with temp_path.open("wb") as f:
            f.write(doc.content)

        file_path = Path("private/files") / doc.attached_to_doctype / doc.attached_to_name / doc.file_name
        save_folder = Path(frappe.get_site_path()) / file_path.parent
        if not save_folder.exists():
            save_folder.mkdir(parents=True)

        doc.file_url = "/" + str(file_path)
        doc.mime_type = mimemapper.get_mime_type(str(temp_path), native_first=False)
        doc.file_type = get_file_type(doc.mime_type)
        manager = FileManager()
        manager.upload_file(temp_path, doc, create_thumbnail=False)

    return doc
