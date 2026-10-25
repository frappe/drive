import shutil
from pathlib import Path
from urllib.parse import urlparse

import frappe
from frappe.core.doctype.file.file import File as FrappeFile
from frappe.core.doctype.file.file import has_permission as ff_has_permission
from frappe.core.doctype.file.utils import get_content_hash
from frappe.utils import now, sbool

from drive.api.files import get_file_type
from drive.api.permissions import get_access, user_has_permission
from drive.api.product import create_invitations
from drive.api.activity import create_new_activity_log

from drive.utils import (
    generate_upward_path,
    get_home_folder,
    get_default_team,
    update_file_size,
    get_new_file_name,
    validate_filename,
    validate_name_on_disk,
    get_upload_path,
    is_site_file,
    ATTACHMENT_CONTENT_DOCTYPE,
    STATUS_ACTIVE,
    STATUS_REMOVED,
)
from drive.utils.files import FileManager
import mimemapper

# Fields that decide which bytes a team file points to, who can reach them, and how much storage it uses.
# Only Drive's own code may change them, and it sets flags.allow_storage_change to say so.
STORAGE_FIELDS = (
    "file_url",
    "file_name",
    "team",
    "folder",
    "is_folder",
    "is_private",
    "file_type",
    "mime_type",
    "status",
    "owner",
    "content_doctype",
    "content_docname",
    "attached_to_doctype",
    "attached_to_name",
    "trash_path",
    "file_size",
    "content_hash",
)


class File(FrappeFile):
    """Team files use Drive's storage/identity rules; Site files (no team) fall
    through to framework `File` behavior."""

    def validate(self):
        previous = self.get_doc_before_save()
        if is_site_file(self) and not (previous and previous.team):
            return super().validate()
        self.validate_storage_fields()
        if frappe.flags.in_patch:
            # Files moved over from older versions keep their names and links
            return
        if self.is_new() or self.has_value_changed("file_name"):
            validate_name_on_disk(self.file_name)
        if self.file_type == "Link" and (self.is_new() or self.has_value_changed("file_url")):
            validate_web_link(self.file_url)

    def validate_storage_fields(self):
        if self.flags.allow_storage_change or frappe.flags.in_patch or frappe.flags.in_install:
            return
        if self.is_new():
            frappe.throw("Files and folders can only be created through Drive.", frappe.PermissionError)
        changed = [field for field in STORAGE_FIELDS if self.has_value_changed(field)]
        if changed:
            frappe.throw(f"These fields can't be changed: {', '.join(changed)}", frappe.PermissionError)

    def before_insert(self):
        # Team files: Drive's upload flow owns storage, so skip core's before_insert.
        if is_site_file(self):
            self.validate_team_file_url()
            return super().before_insert()

    def validate_team_file_url(self):
        """
        A site file may reuse a team file's bytes only if the user can read that team file.
        Other paths inside a team's folder, such as trashed files and thumbnails, can't be reused at all.
        """
        if not self.file_url:
            return
        team_files = frappe.get_all(
            "File",
            filters={"file_url": self.file_url, "team": ["is", "set"], "file_type": ["!=", "Link"]},
            pluck="name",
        )
        if team_files:
            allowed = any(self.can_read_team_file(name) for name in team_files)
        else:
            allowed = not is_in_team_folder(self.file_url)
        if not allowed:
            frappe.throw("You don't have access to this file.", frappe.PermissionError)

    @staticmethod
    def can_read_team_file(name):
        # Desk attachments kept in Drive are also readable by people who can read the document
        doc = frappe.get_doc("File", name)
        return user_has_permission(doc, "read") or ff_has_permission(doc, "read")

    def get_full_path(self):
        if is_site_file(self):
            return super().get_full_path()
        return str(FileManager().resolve(self.file_url))

    def autoname(self):
        if is_site_file(self):
            return super().autoname()
        self.name = getattr(self, "_name", None) or frappe.generate_hash(length=10)

    def after_insert(self):
        if is_site_file(self) or frappe.flags.get("mute_drive_activity_log"):
            return
        full_name = frappe.db.get_value("User", frappe.session.user, "full_name")
        create_new_activity_log(
            entity=self.name,
            activity_type="create",
            activity_message=f"{full_name} created {self.file_name}",
            document_field="file_name",
            field_new_value=self.file_name,
        )

    def after_delete(self):
        if is_site_file(self):
            return

        if self.is_folder:
            for child_name in frappe.get_all("File", filters={"folder": self.name}, pluck="name"):
                frappe.delete_doc("File", child_name, ignore_permissions=True)

        frappe.db.delete("Drive Favourite", {"entity": self.name})
        frappe.db.delete("Drive Entity Log", {"entity_name": self.name})
        frappe.db.delete("Drive Permission", {"entity": self.name})
        frappe.db.delete("Drive Notification", {"notif_doctype_name": self.name})
        frappe.db.delete("Drive Entity Activity Log", {"entity": self.name})

        if (
            self.content_doctype
            and self.content_docname
            and self.content_doctype != ATTACHMENT_CONTENT_DOCTYPE
            and frappe.db.exists(self.content_doctype, self.content_docname)
        ):
            frappe.delete_doc(self.content_doctype, self.content_docname, ignore_permissions=True)

    def on_rollback(self):
        if is_site_file(self) or not self.flags.file_created or not self.file_url or self._not_in_disk():
            return
        path = FileManager().resolve(self.file_url)
        if not path.exists():
            return
        if self.is_folder:
            shutil.rmtree(path)
        else:
            path.unlink()

    def is_downloadable(self):
        # A link's file_url is a web address, never bytes on this site
        if not is_site_file(self) and self.file_type == "Link":
            return False
        return super().is_downloadable()

    def get_content(self, *args, **kwargs):
        if not is_site_file(self) and self.file_type == "Link":
            frappe.throw("Links have no content.", frappe.PermissionError)
        return super().get_content(*args, **kwargs)

    @frappe.whitelist()
    def optimize_file(self):
        if not is_site_file(self):
            frappe.throw("Drive files can't be optimized.", frappe.PermissionError)
        return super().optimize_file()

    def _not_in_disk(self):
        return self.file_type == "Link" or not self.file_url or bool(self.content_doctype)

    # Drive methods
    def _update_modified(func):
        """Used for functions that meaningfuly "modify" a file"""

        def decorator(self, *args, **kwargs):
            # Legacy code
            res = func(self, *args, **kwargs)
            self.db_set("file_modified", now())
            return res

        return decorator

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
            create_invitations(user, auto=True)

        levels = [
            ["read", read],
            ["comment", comment],
            ["share", share],
            ["upload", upload],
            ["write", write],
        ]
        for level, value in levels:
            if sbool(value) and not user_has_permission(self, level):
                frappe.throw("You can't give access that you don't have.", frappe.PermissionError)
        permission.update({l[0]: l[1] for l in levels if l[1] is not None})

        permission.save(ignore_permissions=True)

    def unshare(self, user: str | None = None):
        # Anyone may remove their own access
        if user != frappe.session.user and not user_has_permission(self, "share"):
            frappe.throw("Not permitted to unshare", frappe.PermissionError)

        absolute_path = generate_upward_path(self.name)
        for i in absolute_path:
            if i["owner"] == user:
                frappe.throw("User owns parent folder", frappe.PermissionError)

        if user == "$GENERAL":
            perm_names = frappe.get_all(
                "Drive Permission",
                {"entity": self.name},
                or_filters={"user": "", "team": 1},
                pluck="name",
            )
            for perm_name in perm_names:
                frappe.delete_doc("Drive Permission", perm_name, ignore_permissions=True)

            # If overriding perms of a parent folder, write out an explicit denial
            public_access = get_access(self, "Guest")
            team_access = get_access(self, team=1)
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
                ).insert(ignore_permissions=True)

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

    @_update_modified
    def move(self, new_parent=None, new_team=None):
        """
        Move file to a new folder.
        """
        if new_parent:
            # A file is always in its folder's team. The team is passed in only when moving children,
            # because their new parent has not been saved yet.
            new_team = new_team or frappe.db.get_value("File", new_parent, "team")
        elif new_team:
            new_parent = get_home_folder(new_team).name
        else:
            new_team = self.team
            new_parent = get_home_folder(new_team).name

        if new_parent == self.name:
            frappe.throw(
                "Cannot move into itself",
                ValueError,
            )
        elif not user_has_permission(new_parent, "upload") or not user_has_permission(self, "write"):
            frappe.throw("You don't have permission to move this file.", frappe.PermissionError)

        if not frappe.db.get_value("File", new_parent, "is_folder"):
            frappe.throw(
                "Can only move into folders",
                NotADirectoryError,
            )

        self.flags.allow_storage_change = True

        for child in self.get_children():
            if child.name == self.name or child.name == new_parent:
                frappe.throw(
                    "Cannot move into itself",
                    ValueError,
                )
            elif new_team != child.team:
                child.move(self.name, new_team)

        if new_parent != self.folder:
            old_folder_name = frappe.db.get_value("File", self.folder, "file_name")
            new_folder_name = frappe.db.get_value("File", new_parent, "file_name")
            full_name = frappe.db.get_value("User", frappe.session.user, "full_name")
            create_new_activity_log(
                entity=self.name,
                activity_type="move",
                activity_message=f"{full_name} moved {self.file_name} to {new_folder_name}",
                document_field="folder",
                field_old_value=old_folder_name,
                field_new_value=new_folder_name,
            )

            update_file_size(self.folder, -self.file_size)
            update_file_size(new_parent, +self.file_size)
            self.folder = new_parent
            self.file_name = get_new_file_name(self.file_name, new_parent, self.name)

        self.team = new_team

        # Update all the children's paths
        if not self.manager.flat and not self._not_in_disk():
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

    @_update_modified
    def rename(self, new_file_name: str):
        """
        Rename file or folder
        """
        if not user_has_permission(self, "write"):
            frappe.throw("You cannot rename this file", frappe.PermissionError)

        if new_file_name == self.file_name:
            return self
        validate_filename(new_file_name, self.folder)

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

        self.flags.allow_storage_change = True
        self.file_name = new_file_name
        path = self.manager.rename(self)
        if path and self.file_url and not self._not_in_disk():
            self.recursive_path_move(self.file_url, path)

        self.save()

    def permanent_delete(self):
        write_access = user_has_permission(self, "write")
        parent_write_access = user_has_permission(self.folder, "write")
        if not (write_access or parent_write_access):
            frappe.throw("Not permitted", frappe.PermissionError)

        self.flags.allow_storage_change = True
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
        self.flags.allow_storage_change = True
        if new:
            self.file_url = new
        for child in self.get_children():
            if not child._not_in_disk():
                child.recursive_path_move(
                    child.file_url, str(Path(new) / Path(child.file_url).relative_to(old))
                )
        self.save()

    def get_children(self):
        """Returns a generator that yields child Documents."""
        child_names = frappe.get_all(self.doctype, filters={"folder": self.name}, pluck="name")
        for name in child_names:
            yield frappe.get_doc(self.doctype, name)


def is_in_team_folder(file_url):
    home_folders = frappe.get_all(
        "File",
        filters={"team": ["is", "set"], "is_folder": 1, "folder": ["is", "not set"]},
        pluck="file_url",
    )
    # Teams stored directly in the files folder share it with site files, so they can't be told apart
    return any(
        home and home.rstrip("/") != "/private/files" and file_url.startswith(home.rstrip("/") + "/")
        for home in home_folders
    )


def validate_web_link(url):
    parsed = urlparse(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        frappe.throw("Links must be web addresses that start with http:// or https://.", frappe.ValidationError)


def after_upload_file(doc):
    # frappe handler.upload_file reassigns `doc` to our return value, so always return it.
    if not is_site_file(doc):
        return doc
    settings = frappe.get_single("Drive Disk Settings")
    if frappe.form_dict.library_file_name:
        library_doc = frappe.get_doc("File", frappe.form_dict.library_file_name)
        if not user_has_permission(library_doc, "read"):
            frappe.throw("You don't have access to this file.", frappe.PermissionError)
        doc.team = library_doc.team
        if not is_site_file(doc):
            doc.flags.allow_storage_change = True
            doc.is_private = 1
            doc.folder = get_home_folder(doc.team)["name"]
            doc.file_type = library_doc.file_type
            doc.file_size = library_doc.file_size
            doc.modified = library_doc.modified
            doc.content_doctype = ATTACHMENT_CONTENT_DOCTYPE
            doc.content_docname = frappe.form_dict.library_file_name
    elif settings.use_drive_for_files and doc.attached_to_name:
        # Needs a personal team to place the file in; without one, leave it a Site attachment.
        personal_team = get_default_team()
        if not personal_team:
            return doc
        validate_name_on_disk(doc.file_name)
        manager = FileManager()
        # Keep other attachments with the same name; resolving also keeps the path inside storage
        file_path = Path("private/files") / doc.attached_to_doctype / doc.attached_to_name / doc.file_name
        file_path = manager.get_unused_path(personal_team, file_path)

        doc.flags.allow_storage_change = True
        doc.team = personal_team
        doc.is_private = 1
        content_hash = get_content_hash(doc.content)
        temp_path = get_upload_path("private/files", content_hash[:6] + "-" + Path(file_path).name)
        with temp_path.open("wb") as f:
            f.write(doc.content)

        doc.file_name = Path(file_path).name
        doc.file_url = "/" + str(file_path)
        doc.mime_type = mimemapper.get_mime_type(str(temp_path), native_first=False)
        doc.file_type = get_file_type(doc.mime_type)
        doc.folder = get_home_folder(personal_team)["name"]

        # Thumbnails on by default so attachments look like drive-native files in the grid.
        manager.upload_file(temp_path, doc)

    return doc
