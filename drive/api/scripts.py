import frappe

from drive.api.product import is_admin
from drive.utils import create_drive_file, default_team, get_home_folder, update_file_size
from drive.utils.files import FileManager


@frappe.whitelist()
@default_team
def sync_preview(team: str, json: bool = True):
    manager = FileManager()
    files = manager.fetch_new_files(team)
    sorted_files = sorted(files.items(), key=lambda p: len(p[0].parts))
    # For just checking, strip the root folder
    if json:
        return map(lambda x: (str(x[0]), x[1]), sorted_files)
    return sorted_files


@frappe.whitelist()
@default_team
def sync_from_disk(team: str):
    """
    One-way sync from disk to Drive. Ignores hidden files.
    """
    if not is_admin(team):
        frappe.throw(
            "You do not have permission to sync files from disk.",
            frappe.PermissionError,
        )

    sorted_files = sync_preview(team, json=False)
    files_added = []
    home_folder = get_home_folder(team)["name"]

    def get_or_create_parent(parent_path, owner):
        if not parent_path:
            return home_folder
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
        grandparent = get_or_create_parent(grandparent_path, owner)

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

    for file, (file_size, last_modified, mime_type, actual_path) in sorted_files:
        parent_path = str(file.parent).strip("./")
        parent = frappe.get_value(
            "Drive File",
            {"path": parent_path + "/" if parent_path else "", "team": team},
            "name",
        )
        parent = get_or_create_parent(parent_path, frappe.session.user)

        files_added.append(
            create_drive_file(
                team,
                file.name,
                parent,
                mime_type,
                lambda _: actual_path if mime_type != "folder" else actual_path.strip("/") + "/",
                last_modified=last_modified,
                file_size=file_size,
                is_group=mime_type == "folder",
                owner=frappe.session.user,
            )
        )
        update_file_size(parent, file_size)

    return files_added
