import frappe
from frappe import _
from pypika import functions as fn
from drive.utils.files import get_file_type

MEGA_BYTE = 1024**2
DriveFile = frappe.qb.DocType("Drive File")


@frappe.whitelist()
def storage_breakdown(team, owned_only):
    # Lấy giá trị từ site_config
    site_config = frappe.get_site_config()
    max_storage = site_config.get("plan_limit", {}).get("max_storage_usage")

    if not max_storage:
        frappe.throw(_("max_storage_usage is not configured in site_config"))

    limit = max_storage  # Giữ nguyên đơn vị là byte

    filters = {
        "team": team,
        "is_group": False,
        "is_active": 1,
        "file_size": [">=", limit / 200],
    }

    if owned_only:
        filters["owner"] = frappe.session.user

    entities = frappe.db.get_list(
        "Drive File",
        filters=filters,
        order_by="file_size desc",
        fields=["name", "title", "owner", "file_size", "mime_type", "is_group", "is_link"],
    )

    for r in entities:
        r["file_type"] = get_file_type(r)

    query = (
        frappe.qb.from_(DriveFile)
        .select(DriveFile.mime_type, fn.Sum(DriveFile.file_size).as_("file_size"))
        .where(
            (DriveFile.is_group == 0) &
            (DriveFile.is_active == 1) &
            (DriveFile.team == team)
        )
    )

    if owned_only:
        query = query.where(DriveFile.owner == frappe.session.user)
    else:
        query = query.where(DriveFile.is_private == 0)

    return {
        "limit": limit,
        "total": query.groupby("mime_type").run(as_dict=True),
        "entities": entities,
    }


@frappe.whitelist()
def storage_bar_data(team):
    query = (
        frappe.qb.from_(DriveFile)
        .where(
            (DriveFile.team == team)
            & (DriveFile.is_group == 0)
            & (DriveFile.owner == frappe.session.user)
            & (DriveFile.is_active == 1)
        )
        .select(fn.Coalesce(fn.Sum(DriveFile.file_size), 0).as_("total_size"))
    )

    result = query.run(as_dict=True)[0]
    site_config = frappe.get_site_config()
    plan_limit = site_config.get("plan_limit", {})
    max_storage = plan_limit.get("max_storage_usage")

    result["limit"] = round(max_storage / 1024, 2) if max_storage else 0
    result["unit"] = "GB"
    return result
