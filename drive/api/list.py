import json

import frappe
from pypika import Criterion, CustomFunction, Order
from pypika import functions as fn

from drive.utils import MIME_LIST_MAP, default_team, get_file_type, get_home_folder

from .permissions import ENTITY_FIELDS, get_teams, get_user_access

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
    team,
    entity_name=None,
    order_by="modified 1",
    is_active=1,
    limit=20,
    cursor=None,
    favourites_only=0,
    recents_only=0,
    shared=None,
    tag_list=[],
    file_kinds=[],
    folders=0,
    only_parent=1,
    search=None,
):
    # Clean params
    field, ascending = order_by.replace("modified", "_modified").split(" ")
    is_active = int(is_active)
    only_parent = int(only_parent)
    folders = int(folders)
    favourites_only = int(favourites_only)
    ascending = int(ascending)

    all_teams = False
    if team == "all":
        all_teams = True
        team = None

    if not entity_name and team:
        entity_name = get_home_folder(team)["name"]

    user = frappe.session.user if frappe.session.user != "Guest" else ""
    if entity_name:
        entity = frappe.get_doc("Drive File", entity_name)
        # Verify that entity exists and is part of the team
        if not entity:
            frappe.throw(
                f"Not found ({entity_name}) ",
                frappe.exceptions.PageDoesNotExistError,
            )

        if not team == entity.team:
            team = entity.team

        # Verify that folder is public or that they have access
        user_access = get_user_access(entity, user)

        if not user_access["read"]:
            frappe.throw(
                f"You don't have access.",
                frappe.exceptions.PermissionError,
            )

    query = frappe.qb.from_(DriveFile).where(DriveFile.is_active == is_active)
    if shared:
        cond = (DrivePermission.entity == DriveFile.name) & (
            (DrivePermission.user if shared == "with" else DrivePermission.owner) == frappe.session.user
        )
        # if shared == "with":
        #     teams = get_teams()
        #     cond |= (DrivePermission.team == 1) & (DrivePermission.user.isin(teams))
        query = query.right_join(DrivePermission).on(cond)
    else:
        query = query.left_join(DrivePermission).on(
            (DrivePermission.entity == DriveFile.name) & (DrivePermission.user == user)
        )

    query = query.select(*ENTITY_FIELDS, DrivePermission.user.as_("shared_team")).where(
        fn.Coalesce(DrivePermission.read, 1).as_("read") == 1
    )

    # Cursor pagination
    if cursor:
        query = query.where((Binary(DriveFile[field]) > cursor if ascending else field < cursor)).limit(limit)

    # Cleaner way?
    if only_parent and (not recents_only and not favourites_only and not shared):
        query = query.where(DriveFile.parent_entity == entity_name)
    elif not all_teams:
        query = query.where((DriveFile.team == team) & (DriveFile.parent_entity != ""))

    # Get favourites data (only that, if applicable)
    if favourites_only:
        query = query.right_join(DriveFavourite)
    else:
        query = query.left_join(DriveFavourite)
    query = query.on((DriveFavourite.entity == DriveFile.name) & (DriveFavourite.user == frappe.session.user)).select(
        DriveFavourite.name.as_("is_favourite")
    )

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

    if not is_active:
        query = query.where(DriveFile.owner == frappe.session.user)
    if search:
        # escape wildcards or lower() depending on DB
        query = query.where(DriveFile.title.like(f"%{search}%"))

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
    res = query.run(as_dict=True)

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
        frappe.qb.from_(DrivePermission).where(DrivePermission.user == "").select(DrivePermission.entity)
    )
    team_files_query = frappe.qb.from_(DrivePermission).where(DrivePermission.team == 1).select(DrivePermission.entity)
    public_files = set(k[0] for k in public_files_query.run())
    team_files = set(k[0] for k in team_files_query.run())

    children_count = dict(child_count_query.run())
    share_count = dict(share_query.run())

    default = 0
    if entity_name:
        if get_user_access(entity_name, "Guest")["read"]:
            default = -2
        elif get_user_access(entity_name, team=1)["read"]:
            default = -1

    # Deduplicate
    if shared:
        added = set()
        filtered_list = []
        for r in res:
            if r["name"] not in added:
                filtered_list.append(r)
            added.add(r["name"])
        res = filtered_list

    # Performance hit is wild, manually checking perms each time without cache.
    for r in res:
        r["children"] = children_count.get(r["name"], 0)
        r["file_type"] = get_file_type(r)
        if r["name"] == "1hhf7h7bh2":
            print(r, children_count.get(r["name"], 0))

        if r["name"] in public_files:
            r["share_count"] = -2
        elif default > -1 and (r["name"] in team_files):
            r["share_count"] = -1
        elif default == 0:
            r["share_count"] = share_count.get(r["name"], default)
        else:
            r["share_count"] = default
        r |= get_user_access(r["name"])

    return res
