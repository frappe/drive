import frappe
from frappe.utils.caching import redis_cache

from drive.api.product import is_admin
from drive.utils import create_drive_file, update_file_size
from drive.utils.files import FileManager


@frappe.whitelist()
def sync_preview(team):
    manager = FileManager()
    files = manager.fetch_new_files(team)
    return sorted(files.items(), key=lambda p: len(p[0].parts))


@frappe.whitelist()
def sync_from_disk(team):
    """
    One-way sync from disk to Drive. Ignores hidden files.
    """
    if not is_admin(team):
        frappe.throw(
            "You do not have permission to sync files from disk.",
            frappe.PermissionError,
        )

    sorted_files = sync_preview(team)
    files_added = []

    def get_or_create_parent(parent_path, team, owner):
        # Check if the parent folder exists
        parent = frappe.get_value(
            "Drive File",
            {"path": (parent_path + "/") if parent_path else "", "team": team},
            "name",
        )
        if parent:
            return parent

        # If not, recursively create its own parent first
        grandparent_path = "/".join(parent_path.strip("/").split("/")[:-1])
        grandparent = get_or_create_parent(grandparent_path, team, owner)

        # Now create this parent folder
        new_parent = create_drive_file(
            team,
            title=parent_path.strip("/").split("/")[-1],
            parent=grandparent,
            mime_type="folder",
            entity_path=lambda _: str(parent_path) + "/",
            file_size=0,
            is_group=True,
            owner=owner,
        )
        return new_parent.name

    for file, (file_size, last_modified, mime_type) in sorted_files:
        parent_path = file.parent
        parent = frappe.get_value(
            "Drive File",
            {"path": parent_path + "/" if parent_path else "", "team": team},
            "name",
        )
        parent = get_or_create_parent(parent_path, team, frappe.session.user)
        print("Added", str(file))
        files_added.append(
            create_drive_file(
                team,
                file.name,
                parent,
                mime_type,
                lambda _: str(file) if mime_type != "folder" else str(file).strip("/") + "/",
                last_modified=last_modified,
                file_size=file_size,
                is_group=mime_type == "folder",
                owner=owner,
            )
        )
        update_file_size(parent, file_size)

    return files_added
