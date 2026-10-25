from pathlib import Path
from urllib.parse import unquote

import frappe
from frappe.core.doctype.file.file import File as FrappeFile
from frappe.model.document import Document


class TeamFolderGuard(Document):
    """Added to File with extend_doctype_class, so other apps can extend File too."""

    def before_insert(self):
        # Core copies the bytes at file_url in before_insert, so check first
        validate_not_in_team_folder(self.file_url)
        super().before_insert()


class File(TeamFolderGuard, FrappeFile):
    """For Frappe versions without extend_doctype_class"""


def validate_not_in_team_folder(file_url):
    """
    Drive keeps team files on disk without File records, so core can't check access to them.
    File records can't point inside a team's folder; Drive's own APIs serve those files.
    """
    url = unquote(file_url or "")
    if not url.startswith("/private/files/"):
        return
    root = Path(frappe.get_site_path("private", "files")).resolve()
    path = (root / url.removeprefix("/private/files/")).resolve()
    if any(path.is_relative_to(folder) for folder in get_team_folders(root)):
        frappe.throw("You don't have access to this file.", frappe.PermissionError)


def get_team_folders(root):
    home_paths = frappe.get_all(
        "Drive File",
        filters={"parent_entity": ["is", "not set"], "is_group": 1},
        pluck="path",
    )
    folders = {(root / path).resolve() for path in home_paths if path}
    # Teams stored directly in the files folder share it with site files, so they can't be told apart
    folders.discard(root)
    return folders
