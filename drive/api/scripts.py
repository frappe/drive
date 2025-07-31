import frappe

from drive.utils import create_drive_file, get_parent_path, update_file_size
from drive.utils.files import FileManager


@frappe.whitelist()
def sync_from_disk(team):
    """
    One-way synce from disk to Drive. Ignores hidden files.
    """
    manager = FileManager()

    files_added = []
    files = manager.fetch_new_files(team)
    sorted_files = sorted(files.items(), key=lambda p: len(p[0].parts))
    for file, (loc, file_size, last_modified, mime_type) in sorted_files:
        is_private = loc != "team"
        parent_path = get_parent_path(file, is_private)
        parent = frappe.get_value(
            "Drive File",
            {"path": parent_path, "team": team},
            "name",
        )
        if not parent:
            raise frappe.DoesNotExistError(
                f"Parent folder for {file}, {parent_path}, does not exist in Drive."
            )

        files_added.append(
            create_drive_file(
                team,
                is_private,
                file.name,
                parent,
                mime_type,
                lambda _: str(file),
                last_modified=last_modified,
                file_size=file_size,
                is_group=mime_type == "folder",
                owner=loc if is_private else None,
            )
        )
        update_file_size(parent, file_size)

    return files_added
