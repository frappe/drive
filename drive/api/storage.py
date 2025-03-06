import frappe
from pypika import functions as fn

MEGA_BYTE = 1024**2
DriveFile = frappe.qb.DocType("Drive File")


@frappe.whitelist()
def storage_breakdown(team, owned_only):
    storage = frappe.get_value("Drive Team", team, "quota" if owned_only else "storage")
    filters = {
        "team": team,
        "is_group": False,
        "is_active": 1,
        "file_size": [">", storage / 200 * MEGA_BYTE],
    }
    if owned_only:
        filters["owner"] = frappe.session.user

    entities = frappe.db.get_list(
        "Drive File",
        filters=filters,
        order_by="file_size desc",
        fields=["name", "title", "owner", "file_size", "mime_type"],
    )

    query = (
        frappe.qb.from_(DriveFile)
        .select(DriveFile.mime_type, fn.Sum(DriveFile.file_size).as_("file_size"))
        .where((DriveFile.is_group == 0) & (DriveFile.is_active == 1) & (DriveFile.team == team))
    )
    if owned_only:
        query = query.where(DriveFile.owner == frappe.session.user)
    else:
        query = query.where(DriveFile.is_private == 0)

    return {
        "limit": storage * MEGA_BYTE,
        "entities": entities,
        "total": query.groupby(DriveFile.mime_type).run(as_dict=True),
    }


@frappe.whitelist()
def storage_bar_data(team):
    query = (
        frappe.qb.from_(DriveFile)
        .where(
            (DriveFile.team == team)
            & (DriveFile.owner == frappe.session.user)
            & (DriveFile.is_active == 1)
        )
        .select(fn.Sum(DriveFile.file_size).as_("total_size"))
    )
    result = query.run(as_dict=True)[0]
    result["limit"] = frappe.get_value("Drive Team", team, "quota") * MEGA_BYTE
    return result
