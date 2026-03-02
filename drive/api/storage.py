import frappe
from pypika import functions as fn

from drive.utils import default_team, get_file_type
from drive.api.permissions import user_has_permission

MEGA_BYTE = 1024**2
DriveFile = frappe.qb.DocType("Drive File")


@frappe.whitelist()
def storage_breakdown(team: str, owned_only: bool):
    limit = frappe.get_value("Drive Team", team, "quota" if owned_only else "storage") * MEGA_BYTE
    filters = {
        "team": team,
        "is_group": False,
        "is_active": 1,
        "file_size": [">=", limit / 200],
    }
    if owned_only:
        filters["owner"] = frappe.session.user

    # Get is_link because file type check requires it
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
        .where((DriveFile.is_group == 0) & (DriveFile.is_active == 1) & (DriveFile.team == team))
    )
    if owned_only:
        query = query.where(DriveFile.owner == frappe.session.user)

    return {
        "limit": limit,
        "total": query.groupby(DriveFile.mime_type).run(as_dict=True),
        "entities": entities,
    }


@frappe.whitelist()
@default_team
def storage_bar_data(team: str | None = None, entity_name: str | None = None):
    if not team:
        team = frappe.get_value("Drive File", entity_name, "team")
        if not team:
            frappe.throw("Could not find team.", ValueError)
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
    result["limit"] = frappe.get_value("Drive Team", team, "quota") * MEGA_BYTE
    return result
