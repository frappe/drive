import frappe
from pathlib import Path
from pypika import functions as fn
import os
import json


@frappe.whitelist()
def get_max_storage():
    """
    Retrieves the maximum storage limit for the user's plan.
    The storage limit is returned in bytes, with a block size of 1024.

    Returns:
        int: The maximum storage limit in bytes.
    """
    storage_quota_enabled = frappe.db.get_single_value(
        "Drive Instance Settings", "enable_user_storage_quota"
    )
    plan_limit = frappe.conf.get("plan_limit")
    if plan_limit:
        max_storage = plan_limit["max_storage_usage"]
        max_storage = int(max_storage)
    if not plan_limit:
        val = frappe.conf.get("max_storage")
        if not val:
            add_new_site_config_key("max_storage", 5120)
        max_storage = frappe.conf.get("max_storage")
        max_storage = int(max_storage)
    max_storage = max_storage * 1024**2
    if storage_quota_enabled and (quota := validate_quota()):
        return {"quota": quota, "limit": max_storage}
    return {"limit": max_storage}


def validate_quota():
    """
    Fetch user storage quota
    formatted the same as `get_max_storage()`
    """
    quota_limit = frappe.db.get_value(
        "Drive User Storage Quota",
        {"User": frappe.session.user},
        ["user_storage_limit"],
    )
    if quota_limit:
        return int(quota_limit * 1024**2)


@frappe.whitelist()
def get_owned_files_by_storage():
    entities = frappe.db.get_list(
        "Drive Entity",
        filters={"owner": frappe.session.user, "is_group": False},
        order_by="file_size desc",
        fields=["name", "title", "owner", "file_size", "file_kind", "mime_type"],
    )
    DriveEntity = frappe.qb.DocType("Drive Entity")
    query = (
        frappe.qb.from_(DriveEntity)
        .select(DriveEntity.file_kind, fn.Sum(DriveEntity.file_size).as_("file_size"))
        .where((DriveEntity.is_group == 0) & (DriveEntity.owner == frappe.session.user))
        .groupby(DriveEntity.file_kind)
    )
    total = query.run(as_dict=True)
    return {"entities": entities, "total": total}


@frappe.whitelist()
def total_storage_used():
    DriveEntity = frappe.qb.DocType("Drive Entity")
    query = frappe.qb.from_(DriveEntity).select(fn.Sum(DriveEntity.file_size).as_("total_size"))
    result = query.run(as_dict=True)
    return result


@frappe.whitelist()
def total_storage_used_by_user():
    DriveEntity = frappe.qb.DocType("Drive Entity")
    query = (
        frappe.qb.from_(DriveEntity)
        .where(DriveEntity.owner == frappe.session.user)
        .select(fn.Sum(DriveEntity.file_size).as_("total_size"))
    )
    result = query.run(as_dict=True)
    return result


@frappe.whitelist()
def total_storage_used_by_file_kind():
    DriveEntity = frappe.qb.DocType("Drive Entity")
    query = (
        frappe.qb.from_(DriveEntity)
        .select(DriveEntity.file_kind, fn.Sum(DriveEntity.file_size).as_("total_size"))
        .where(DriveEntity.is_group == 0)
        .groupby(DriveEntity.file_kind)
    )
    return query.run(as_dict=True)


def get_storage_allowed():
    limit = get_max_storage()
    total_limit = int(limit.get("limit"))
    total_usage = int(total_storage_used()[0].total_size or 0)
    total_rem = total_limit - total_usage
    if limit.get("quota") is not None:
        quota_limit = int(limit.get("quota"))
        usr_usage = int(total_storage_used_by_user()[0].total_size or 0)
        usr_rem = quota_limit - usr_usage
        return min(usr_rem, total_rem)
    else:
        return total_rem
    


def total_disk_storage_used():
    try:
        from drive.utils.files import get_user_directory

        user_directory = get_user_directory()
        # -sb doesnt work on macos
        cmd = f"du -sb {Path(user_directory.path)} | cut -f1"
        result = os.popen(cmd)
        size = result.read().strip()
    except:
        size = "0M"
    return size


def add_new_site_config_key(key, val):
    site_path = frappe.get_site_path()
    site_config_path = os.path.join(site_path, "site_config.json")

    with open(site_config_path, "r") as f:
        site_config = json.load(f)

    site_config[str(key)] = str(val)

    with open(site_config_path, "w") as f:
        json.dump(site_config, f, indent=2)
