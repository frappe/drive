import os, json

import frappe
from pypika import functions as fn

DriveFile = frappe.qb.DocType("Drive File")


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
        print(val)
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
def storage_breakdown_owned(team):
    storage = frappe.get_value("Drive Team", team, "quota")
    entities = frappe.db.get_list(
        "Drive File",
        filters={"owner": frappe.session.user, "team": team, "is_group": False, "is_active": 1},
        order_by="file_size desc",
        fields=["name", "title", "owner", "file_size", "mime_type"],
    )
    query = (
        frappe.qb.from_(DriveFile)
        .select(DriveFile.mime_type, fn.Sum(DriveFile.file_size).as_("file_size"))
        .where(
            (DriveFile.is_group == 0)
            & (DriveFile.is_active == 1)
            & (DriveFile.owner == frappe.session.user)
            & (DriveFile.team == team)
        )
        .groupby(DriveFile.mime_type)
    )
    total = query.run(as_dict=True)
    return {"entities": entities, "total": total, "limit": storage * 1024**2}


@frappe.whitelist()
def storage_breakdown_team(team):
    storage = frappe.get_value("Drive Team", team, "storage")
    entities = frappe.db.get_list(
        "Drive File",
        filters={"team": team, "is_group": False, "is_active": 1},
        order_by="file_size desc",
        fields=["name", "title", "owner", "file_size", "mime_type"],
    )
    query = (
        frappe.qb.from_(DriveFile)
        .select(DriveFile.mime_type, fn.Sum(DriveFile.file_size).as_("file_size"))
        .where((DriveFile.is_group == 0) & (DriveFile.is_active == 1) & (DriveFile.team == team))
        .groupby(DriveFile.mime_type)
    )
    total = query.run(as_dict=True)
    return {"entities": entities, "total": total, "limit": storage * 1024**2}


@frappe.whitelist()
def total_storage_used(team):
    query = (
        frappe.qb.from_(DriveFile)
        .where(DriveFile.team == team)
        .select(fn.Sum(DriveFile.file_size).as_("total_size"))
    )
    result = query.run(as_dict=True)
    result[0].update(get_max_storage())
    return result[0]


@frappe.whitelist()
def total_storage_used_by_user():
    query = (
        frappe.qb.from_(DriveFile)
        .where(DriveFile.owner == frappe.session.user)
        .select(fn.Sum(DriveFile.file_size).as_("total_size"))
    )
    result = query.run(as_dict=True)
    return result


def get_storage_allowed(team):
    limit = get_max_storage()
    total_limit = int(limit.get("limit"))
    total_usage = int(total_storage_used(team).total_size or 0)
    total_rem = total_limit - total_usage
    if limit.get("quota") is not None:
        quota_limit = int(limit.get("quota"))
        usr_usage = int(total_storage_used_by_user()[0].total_size or 0)
        usr_rem = quota_limit - usr_usage
        return min(usr_rem, total_rem)
    else:
        return total_rem


def add_new_site_config_key(key, val):
    site_path = frappe.get_site_path()
    site_config_path = os.path.join(site_path, "site_config.json")

    with open(site_config_path, "r") as f:
        site_config = json.load(f)

    site_config[str(key)] = str(val)

    with open(site_config_path, "w") as f:
        json.dump(site_config, f, indent=2)
