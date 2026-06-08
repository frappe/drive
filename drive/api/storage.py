import frappe
from pypika import functions as fn

from drive.utils import default_team, STATUS_ACTIVE

MEGA_BYTE = 1024**2
DriveFile = frappe.qb.DocType("File")


@frappe.whitelist()
def storage_breakdown(team: str, owned_only: bool):
    limit = frappe.get_value("Drive Team", team, "quota" if owned_only else "storage") * MEGA_BYTE
    filters = {
        "team": team,
        "is_folder": False,
        "status": STATUS_ACTIVE,
        "file_size": [">=", limit / 200],
    }
    if owned_only:
        filters["owner"] = frappe.session.user

    entities = frappe.db.get_list(
        "File",
        filters=filters,
        order_by="file_size desc",
        fields=["name", "file_name", "owner", "file_size", "file_type"],
    )

    query = (
        frappe.qb.from_(DriveFile)
        .select(DriveFile.file_type, fn.Sum(DriveFile.file_size).as_("file_size"))
        .where((DriveFile.is_folder == 0) & (DriveFile.status == STATUS_ACTIVE) & (DriveFile.team == team))
    )
    if owned_only:
        query = query.where(DriveFile.owner == frappe.session.user)

    return {
        "limit": limit,
        "total": query.groupby(DriveFile.file_type).run(as_dict=True),
        "entities": entities,
    }


@frappe.whitelist()
@default_team
def storage_bar_data(team: str | None = None, entity_name: str | None = None):
    if not team:
        team = frappe.get_value("File", entity_name, "team")
        if not team:
            frappe.throw("Could not find team.", ValueError)

    query = (
        frappe.qb.from_(DriveFile)
        .where(
            (DriveFile.team == team)
            & (DriveFile.is_folder == 0)
            & (DriveFile.owner == frappe.session.user)
            & (DriveFile.status == STATUS_ACTIVE)
        )
        .select(fn.Coalesce(fn.Sum(DriveFile.file_size), 0).as_("total_size"))
    )
    result = query.run(as_dict=True)[0]
    result["limit"] = frappe.get_value("Drive Team", team, "quota") * MEGA_BYTE
    return result
