import json

import frappe
from pypika import Criterion, CustomFunction, Order
from pypika import functions as fn

from drive.utils import MIME_LIST_MAP, default_team, get_file_type, get_home_folder

from .permissions import ENTITY_FIELDS, get_user_access

DriveUser = frappe.qb.DocType("User")
UserGroupMember = frappe.qb.DocType("User Group Member")
DriveFile = frappe.qb.DocType("Drive File")
DrivePermission = frappe.qb.DocType("Drive Permission")
Team = frappe.qb.DocType("Drive Team")
TeamMember = frappe.qb.DocType("Drive Team Member")
DriveFavourite = frappe.qb.DocType("Drive Favourite")
Recents = frappe.qb.DocType("Drive Entity Log")
DriveEntityTag = frappe.qb.DocType("Drive Entity Tag")

Binary = CustomFunction("BINARY", ["expression"])


@frappe.whitelist(allow_guest=True)
@default_team
def files(
    team=None,
    entity_name=None,
    order_by="modified 1",
    is_active=1,
    limit=20,
    cursor=None,
    favourites_only=0,
    recents_only=0,
    tag_list=[],
    file_kinds=[],
    personal=-1,
    folders=0,
    only_parent=1,
    search=None,
):

    field, ascending = order_by.replace("modified", "_modified").split(" ")
    is_active = int(is_active)
    only_parent = int(only_parent)
    folders = int(folders)
    personal = int(personal)
    favourites_only = int(favourites_only)
    ascending = int(ascending)

    if not entity_name:
        entity_name = get_home_folder(team)["name"]

    entity = frappe.get_doc("Drive File", entity_name)
    # Verify that entity exists and is part of the team
    if not entity:
        frappe.throw(
            f"Not found ({entity_name}) ",
            frappe.exceptions.PageDoesNotExistError,
        )

    if not team == entity.team:
        team = entity.team
    home = get_home_folder(team)["name"]

    # Verify that folder is public or that they have access
    user = frappe.session.user if frappe.session.user != "Guest" else ""
    user_access = get_user_access(entity, user)

    if not user_access["read"]:
        frappe.throw(
            f"You don't have access.",
            frappe.exceptions.PermissionError,
        )
    query = (
        frappe.qb.from_(DriveFile)
        .where(DriveFile.is_active == is_active)
        .left_join(DrivePermission)
        .on((DrivePermission.entity == DriveFile.name) & (DrivePermission.user == user))
        # Give defaults as a team member
        .select(*ENTITY_FIELDS, "team")
        .where(fn.Coalesce(DrivePermission.read, user_access["read"]).as_("read") == 1)
    )

    # Cursor pagination
    if cursor:
        query = query.where(
            (Binary(DriveFile[field]) > cursor if ascending else field < cursor)
        ).limit(limit)

    if only_parent and (not recents_only and not favourites_only):
        query = query.where(DriveFile.parent_entity == entity_name)
    else:
        query = query.where((DriveFile.team == team) & (DriveFile.parent_entity != ""))

    # Get favourites data (only that, if applicable)
    if favourites_only:
        query = query.right_join(DriveFavourite)
    else:
        query = query.left_join(DriveFavourite)
    query = query.on(
        (DriveFavourite.entity == DriveFile.name) & (DriveFavourite.user == frappe.session.user)
    ).select(DriveFavourite.name.as_("is_favourite"))

    if recents_only:
        query = (
            query.right_join(Recents)
            .on((Recents.entity_name == DriveFile.name) & (Recents.user == frappe.session.user))
            .orderby(Recents.last_interaction, order=Order.desc)
        )
    else:
        query = (
            query.left_join(Recents)
            .on((Recents.entity_name == DriveFile.name) & (Recents.user == frappe.session.user))
            .orderby(DriveFile[field], order=Order.asc if ascending else Order.desc)
        )

    if favourites_only or recents_only:
        query = query.where((DriveFile.is_private == 0) | (DriveFile.owner == frappe.session.user))
    elif not is_active:
        query = query.where(DriveFile.owner == frappe.session.user)
    if search:
        # escape wildcards or lower() depending on DB
        query = query.where(DriveFile.title.like(f"%{search}%"))
    if personal == 0:
        query = query.where(DriveFile.is_private == 0)
    elif personal == 1:
        query = query.where(DriveFile.is_private == 1)
        # Temporary hack: the correct way would be to check permissions on all children
        if entity_name == home:
            query = query.where(DriveFile.owner == frappe.session.user)
    # Only filter in home folder; previously private shared folders showed up empty
    elif personal == -1 and entity_name == home:
        query = query.where(
            (DriveFile.is_private == 0)
            | ((DriveFile.is_private == 1) & (DriveFile.owner == frappe.session.user))
        )

    query = query.select(Recents.last_interaction.as_("accessed"))
    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveFile.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    file_kinds = json.loads(file_kinds) if not isinstance(file_kinds, list) else file_kinds
    if file_kinds:
        mime_types = []
        for kind in file_kinds:
            mime_types.extend(MIME_LIST_MAP.get(kind, []))
        criterion = [DriveFile.mime_type == mime_type for mime_type in mime_types]
        if "Folder" in file_kinds:
            criterion.append(DriveFile.is_group == 1)
        query = query.where(Criterion.any(criterion))

    if folders:
        query = query.where(DriveFile.is_group == 1)

    child_count_query = (
        frappe.qb.from_(DriveFile)
        .where((DriveFile.team == team) & (DriveFile.is_active == 1))
        .select(DriveFile.parent_entity, fn.Count("*").as_("child_count"))
        .groupby(DriveFile.parent_entity)
    )
    share_query = (
        frappe.qb.from_(DriveFile)
        .right_join(DrivePermission)
        .on(DrivePermission.entity == DriveFile.name)
        .where((DrivePermission.user != "") & (DrivePermission.user != "$TEAM"))
        .select(DriveFile.name, fn.Count("*").as_("share_count"))
        .groupby(DriveFile.name)
    )
    public_files_query = (
        frappe.qb.from_(DrivePermission)
        .where(DrivePermission.user == "")
        .select(DrivePermission.entity)
    )
    team_files_query = (
        frappe.qb.from_(DrivePermission)
        .where(DrivePermission.user == "$TEAM")
        .select(DrivePermission.entity)
    )
    public_files = set(k[0] for k in public_files_query.run())
    team_files = set(k[0] for k in team_files_query.run())

    children_count = dict(child_count_query.run())
    share_count = dict(share_query.run())
    res = query.run(as_dict=True)
    default = 0
    if get_user_access(entity_name, "Guest")["read"]:
        default = -2
    elif get_user_access(entity_name, "$TEAM")["read"]:
        default = -1

    for r in res:
        r["children"] = children_count.get(r["name"], 0)
        r["file_type"] = get_file_type(r)

        if r["name"] in public_files:
            r["share_count"] = -2
        elif default > -1 and (r["name"] in team_files or not r["is_private"]):
            r["share_count"] = -1
        elif default == 0:
            r["share_count"] = share_count.get(r["name"], default)
        else:
            r["share_count"] = default

        r |= get_user_access(r["name"])

    return res


@frappe.whitelist()
def shared(
    by=0,
    order_by="modified",
    limit=1000,
    tag_list=[],
    mime_type_list=[],
    public=0,
    team=None,
):
    """
    Returns the highest level of shared items shared with/by the current user, group or org

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveFile doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """
    by = int(by)
    public = int(public)
    query = (
        frappe.qb.from_(DriveFile)
        .right_join(DrivePermission)
        .on(
            (DrivePermission.entity == DriveFile.name)
            & (
                (DrivePermission.owner if by else DrivePermission.user)
                == ("" if public else frappe.session.user)
            )
        )
        .limit(limit)
        .where((DrivePermission.read == 1) & (DriveFile.is_active == 1))
        .select(
            *ENTITY_FIELDS,
            DriveFile.team,
            DrivePermission.user,
            DrivePermission.owner.as_("sharer"),
            DrivePermission.read,
            DrivePermission.share,
            DrivePermission.comment,
            DrivePermission.write,
        )
    )

    query = query.orderby(
        order_by.split()[0],
        order=Order.desc if order_by.endswith("desc") else Order.asc,
    )

    if team:
        query = query.where(DriveFile.team == team)

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveFile.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        query = query.where(
            Criterion.any(DriveFile.mime_type == mime_type for mime_type in mime_type_list)
        )

    # Extremely inefficient
    child_count_query = (
        frappe.qb.from_(DriveFile)
        .where((DriveFile.is_active == 1))
        .select(DriveFile.parent_entity, fn.Count("*").as_("child_count"))
        .groupby(DriveFile.parent_entity)
    )
    share_query = (
        frappe.qb.from_(DriveFile)
        .right_join(DrivePermission)
        .on(DrivePermission.entity == DriveFile.name)
        .where((DrivePermission.user != "") & (DrivePermission.user != "$TEAM"))
        .select(DriveFile.name, fn.Count("*").as_("share_count"))
        .groupby(DriveFile.name)
    )
    public_files_query = (
        frappe.qb.from_(DrivePermission)
        .where(DrivePermission.user == "")
        .select(DrivePermission.entity)
    )
    team_files_query = (
        frappe.qb.from_(DrivePermission)
        .where(DrivePermission.user == "$TEAM")
        .select(DrivePermission.entity)
    )
    public_files = set(k[0] for k in public_files_query.run())
    team_files = set(k[0] for k in team_files_query.run())

    children_count = dict(child_count_query.run())
    share_count = dict(share_query.run())
    res = query.run(as_dict=True)
    parents = {r["name"] for r in res}

    for r in res:
        r["children"] = children_count.get(r["name"], 0)
        r["file_type"] = get_file_type(r)
        if r["name"] in public_files:
            r["share_count"] = -2
        elif r["name"] in team_files:
            r["share_count"] = -1
        else:
            r["share_count"] = share_count.get(r["name"], 0)

    return [r for r in res if r["parent_entity"] not in parents]
