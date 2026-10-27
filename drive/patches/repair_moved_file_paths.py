from collections import defaultdict
from pathlib import Path

import frappe

from drive.utils.files import FileManager


def execute():
    """
    Renaming, moving or restoring a folder moved everything in it on disk, but only updated the stored path
    of files that the user who did it owned. Point those files, and folders, at where they are now.
    Only changes a path when nothing is at the stored path and the file is where its folder says it should be.
    """
    manager = FileManager()
    if manager.flat or manager.s3_enabled:
        return

    children = defaultdict(list)
    for entity in frappe.get_all(
        "Drive File",
        filters={"is_active": 1},
        fields=["name", "title", "parent_entity", "path", "is_group", "is_link", "document", "mime_type"],
    ):
        children[entity.parent_entity or ""].append(entity)

    # Top-down from the team folders, so that a repaired folder's path is used for what is inside it
    folders = [(root.name, root.path) for root in children[""] if root.is_group and root.path]
    while folders:
        folder, folder_path = folders.pop()
        for entity in children[folder]:
            if entity.is_link or entity.document or entity.mime_type == "frappe/slides" or not entity.path:
                continue
            expected = str(Path(folder_path) / entity.title)
            if entity.path != expected and not on_disk(manager, entity.path) and on_disk(manager, expected):
                frappe.db.set_value("Drive File", entity.name, "path", expected, update_modified=False)
                entity.path = expected
            if entity.is_group:
                folders.append((entity.name, entity.path))


def on_disk(manager, path):
    try:
        return manager.resolve(path).exists()
    except frappe.PermissionError:
        # A path outside Drive's storage. Leave it alone rather than stop the migration.
        return False
