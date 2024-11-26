import frappe
import os
import shutil
from pathlib import Path


def execute():
    """
    Add a root directory for Frappe Drive
    Move all files to this new directory
    Update all file DB records to point to these files
    """
    root_name = "FD_data"
    create_root_directory(root_name)
    root_folders = get_root_entities()
    files = get_non_root_entities()
    site_root = frappe.get_site_path("private/files")
    move_root_folders(root_folders, site_root, root_name)
    move_non_root(files, site_root, root_name)


def create_root_directory(root_name):
    """ 
    Create new root FD_data
    """
    file_path = frappe.get_site_path("private/files/")
    file_path += root_name
    os.makedirs(file_path, exist_ok=True)


def get_root_entities():
    """  
    Fetch all user directories
    """
    DriveEntity = frappe.qb.DocType("Drive Entity")
    selectedFields = [
        DriveEntity.title,
        DriveEntity.name,
        DriveEntity.path,
        DriveEntity.owner,
        DriveEntity.title,
        DriveEntity.is_group,
    ]
    query = (
        frappe.qb.from_(DriveEntity)
        .select(*selectedFields)
        .where((DriveEntity.parent_drive_entity.isnull()) & (DriveEntity.is_group == 1))
    )
    result = query.run(as_dict=True)
    return result


def get_non_root_entities():
    """ 
    Get all non root entities
    """
    DriveEntity = frappe.qb.DocType("Drive Entity")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.path,
        DriveEntity.owner,
        DriveEntity.title,
        DriveEntity.is_group,
    ]
    query = (
        frappe.qb.from_(DriveEntity)
        .select(*selectedFields)
        .where(
            (DriveEntity.parent_drive_entity.notnull())
            & (DriveEntity.path.notnull())
            & (DriveEntity.is_active == 1)
        )
    )
    result = query.run(as_dict=True)
    return result


def move_root_folders(root_folders, site_root, root_name):
    """ 
    Move user directories to /FD_data
    Make /files inside each
    Update DB path for user dirs
    """
    for folder in root_folders:
        folder_name = Path(folder["path"]).parts[-1]
        new_db_path = f"/{root_name}/{folder_name}/"
        curr_fs_path = site_root + f"/{folder_name}/"
        new_fs_path = site_root + new_db_path

        os.makedirs(curr_fs_path + "files", exist_ok=True)

        shutil.move(curr_fs_path, new_fs_path)
        frappe.db.set_value(
           "Drive Entity", folder["name"], "path", new_db_path, update_modified=False
        )


def move_non_root(files, site_root, root_name):
    """  
    move all user files to /FD_data/files
    update embeds DB path
    update db path to relative /files/$NAME
    """
    for file in files:
        entity_name = file["name"]

        curr_db_path = Path(file["path"])
        curr_db_split = list(curr_db_path.parts)

        idx = curr_db_split.index("files")
        user_dir = curr_db_split[idx + 1] if idx + 1 < len(curr_db_split) else None

        if "embeds" in curr_db_split:
            new_db_path = list(curr_db_split[-2:])

        elif "uploads" in curr_db_split:
            new_db_path = list(curr_db_split[-2:])
        else:
            # Fix current src FC directory
            curr_fs_path = curr_db_split[-1:]
            curr_fs_path.insert(0, user_dir)
            curr_fs_path.insert(0, f"/{root_name}")

            # single level DB path
            new_db_path = curr_db_split[-1:]
            new_db_path.insert(0, "files")

            # new FS path at FD_data/$user_dir/files
            new_fs_path = new_db_path.copy()
            new_fs_path.insert(0, user_dir)
            new_fs_path.insert(0, f"/{root_name}")

            new_fs_path = Path(*new_fs_path)
            curr_fs_path = Path(*curr_fs_path)

            # str to preserve "./"
            new = site_root + str(new_fs_path)
            curr = site_root + str(curr_fs_path)
            
            shutil.move(curr, new)
        
        new_db_path = Path(*new_db_path)
        db = str(new_db_path)
        frappe.db.set_value(
           "Drive Entity", entity_name, "path", db, update_modified=False
        )
