import frappe
import json
from drive.utils.files import get_home_folder, MIME_LIST_MAP, get_file_type
from .permissions import ENTITY_FIELDS, get_user_access, get_teams
from pypika import Order, Criterion, functions as fn, CustomFunction


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
def files(
    team,
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
):
    home = get_home_folder(team)["name"]
    field, ascending = order_by.split(" ")
    is_active = int(is_active)
    only_parent = int(only_parent)
    folders = int(folders)
    personal = int(personal)
    ascending = int(ascending)

    if not entity_name:
        # If not specified, get home folder
        entity_name = home
    entity = frappe.get_doc("Drive File", entity_name)

    # Verify that entity exists and is part of the team
    if not entity or entity.team != team:
        frappe.throw(
            f"Not found - entity {entity_name} has team {team} ",
            frappe.exceptions.PageDoesNotExistError,
        )

    # Verify that folder is public or that they have access
    user = frappe.session.user if frappe.session.user != "Guest" else ""
    user_access = get_user_access(entity, user)
    if not user_access["read"]:
        frappe.throw(
            f"You don't have access.",
            frappe.exceptions.PageDoesNotExistError,
        )
    query = (
        frappe.qb.from_(DriveFile)
        .where(DriveFile.is_active == is_active)
        .left_join(DrivePermission)
        .on((DrivePermission.entity == DriveFile.name) & (DrivePermission.user == user))
        # Give defaults as a team member
        .select(
            *ENTITY_FIELDS,
        )
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

    if personal == 0:
        query = query.where(DriveFile.is_private == 0)
    elif personal == 1:
        query = query.where(DriveFile.is_private == 1)
        # Temporary hack: the correct way would be to check permissions on all children
        if entity_name == home:
            query = query.where(DriveFile.owner == frappe.session.user)
    elif personal == -1:
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
    for r in res:
        r["children"] = children_count.get(r["name"], 0)
        r["file_type"] = get_file_type(r)
        if r["name"] in public_files:
            r["share_count"] = -2
        elif r["name"] in team_files:
            r["share_count"] = -1
        else:
            r["share_count"] = share_count.get(r["name"], 0)
        r |= get_user_access(r["name"])
        print(r)

    return res


@frappe.whitelist()
def shared(
    by=0,
    order_by="modified",
    limit=1000,
    tag_list=[],
    mime_type_list=[],
):
    """
    Returns the highest level of shared items shared with/by the current user, group or org

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveFile doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """
    by = int(by)
    query = (
        frappe.qb.from_(DriveFile)
        .right_join(DrivePermission)
        .on(
            (DrivePermission.entity == DriveFile.name)
            & ((DrivePermission.owner if by else DrivePermission.user) == frappe.session.user)
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


# @frappe.whitelist()
# def files_for_move(
#     team,
#     is_private
# ):
#     """
#     A light version that can support recursiveness
#     """
#     if not entity_name:
#         home = get_home_folder(team)["name"]
#         # If not specified, get home folder
#         entity_name = home
#     user = frappe.db.escape(frappe.session.user)
#     entity_name = frappe.db.escape(entity_name)

#         f"""
#         WITH RECURSIVE file_tree AS (
#             SELECT
#                 f.name,
#                 f.title,
#                 f.is_group,
#                 f.parent_entity,
#                 f.owner,
#                 f.is_private
#             FROM DriveFile f
#             WHERE f.id = {entity_name}
#             UNION ALL

#             SELECT
#                 child.name,
#                 child.title,
#                 child.is_group,
#                 child.parent_entity,
#                 child.owner,
#                 child.is_private
#             FROM DriveFile child
#             JOIN file_tree parent ON child.parent_entity = parent.name
#         )
#         file_with_permission AS (
#             SELECT
#                 ft.*,
#                 COALESCE(
#                     p.write,
#                     CASE
#                         WHEN ft.is_private = 0 THEN 1
#                         WHEN ft.owner = {user} THEN 1
#                         ELSE 0
#                     END
#                 ) AS write
#             FROM file_tree ft
#             LEFT JOIN DrivePermission p ON p.entity = ft.name AND p.user = {user}
#         )
#         SELECT * FROM file_with_permission;
#     """,
#         as_dict=1,
#     )
#     print(res)
#     return res
