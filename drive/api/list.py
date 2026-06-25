import json
from collections import Counter

import frappe
from pypika import Criterion, CustomFunction, Order
from pypika import functions as fn


from drive.utils import (
    MIME_LIST_MAP,
    default_team,
    get_home_folder,
    FILE_FIELDS,
    map_ff_to_drive_type,
    entity_kind,
    hide_storage_key,
    is_site_file,
    KIND_VIRTUAL,
    STATUS_ACTIVE,
    STATUS_TRASHED,
)
from drive.utils.api import get_default_access
from .permissions import get_user_access, user_has_permission, get_teams

DriveUser = frappe.qb.DocType("User")
UserGroupMember = frappe.qb.DocType("User Group Member")
DriveFile = frappe.qb.DocType("File")
DrivePermission = frappe.qb.DocType("Drive Permission")
Team = frappe.qb.DocType("Drive Team")
TeamMember = frappe.qb.DocType("Drive Team Member")
DriveFavourite = frappe.qb.DocType("Drive Favourite")
Recents = frappe.qb.DocType("Drive Entity Log")

Binary = CustomFunction("BINARY", ["expression"])


# Helper Functions for Filters
def _apply_shared_filter(query, shared_type):
    """
    Filters query to show shared files based on shared_type parameter.
    - "with": files shared with current user
    - "public": publicly shared files
    - False/None: all files with permission join
    """
    user = frappe.session.user if frappe.session.user != "Guest" else ""
    cond = (DrivePermission.entity == DriveFile.name) & (DrivePermission.user == user)

    if shared_type == "with":
        return query.right_join(DrivePermission).on(cond)
    elif shared_type == "public":
        cond = (DrivePermission.entity == DriveFile.name) & (DrivePermission.user == "")
        return query.right_join(DrivePermission).on(cond)
    else:
        return query.left_join(DrivePermission).on(cond)


def _apply_file_kinds_filter(query, file_kinds):
    """
    Filters files by kind/mime type.
    """
    file_kinds = json.loads(file_kinds) if isinstance(file_kinds, str) else file_kinds
    if not file_kinds:
        return query

    mime_types = []
    for kind in file_kinds:
        mime_types.extend(MIME_LIST_MAP.get(kind, []))

    criterion = [DriveFile.mime_type == mime_type for mime_type in mime_types]
    if "Folder" in file_kinds:
        criterion.append(DriveFile.is_folder == 1)

    return query.where(Criterion.any(criterion))


# Data Aggregation Functions
def _get_children_count(files):
    """
    Returns a dict mapping folder names to their child count.
    """
    if not files:
        return {}
    query = (
        frappe.qb.from_(DriveFile)
        .where((DriveFile.folder.isin([k["name"] for k in files])) & (DriveFile.status == STATUS_ACTIVE))
        .groupby(DriveFile.folder)
        .select(DriveFile.folder, fn.Count("*").as_("child_count"))
    )
    return dict(query.run())


def _get_share_count(names):
    """
    Returns a dict mapping file names to their share count.
    Counts shares with individual users (excludes team and public shares).
    """
    if not names:
        return {}
    query = (
        frappe.qb.from_(DriveFile)
        .right_join(DrivePermission)
        .on(DrivePermission.entity == DriveFile.name)
        .where(
            DrivePermission.entity.isin(names)
            & (DrivePermission.user != "")
            & (DrivePermission.user != "$TEAM")
        )
        .select(DriveFile.name, fn.Count("*").as_("share_count"))
        .groupby(DriveFile.name)
    )
    return dict(query.run())


def _get_public_files(names):
    """
    Returns a set of file names that are publicly shared.
    """
    if not names:
        return set()
    query = (
        frappe.qb.from_(DrivePermission)
        .where((DrivePermission.entity.isin(names)) & (DrivePermission.user == ""))
        .select(DrivePermission.entity)
    )
    return set(k[0] for k in query.run())


def _get_team_files(names):
    """
    Returns a set of file names shared with team.
    """
    if not names:
        return set()
    query = (
        frappe.qb.from_(DrivePermission)
        .where((DrivePermission.entity.isin(names)) & (DrivePermission.team == 1))
        .select(DrivePermission.entity)
    )
    return set(k[0] for k in query.run())


def _get_basic_query(search):
    # Status defaults to Active for team and Site files alike — no team carve-out.
    query = frappe.qb.from_(DriveFile).where(DriveFile.status == STATUS_ACTIVE)
    if search:
        query = query.where(DriveFile.file_name.like(f"%{search}%"))
    return query


@frappe.whitelist(allow_guest=True)
@default_team
def files(
    team: str,
    entity_name: str | None = None,
    order_by: str = "modified",
    ascending: bool = True,
    file_kinds: list[str] | str = [],
    search: str = None,
    start: int = 0,
    limit: int = None,
):
    """
    Returns active files in a folder. Pass `start`/`limit` to page through large
    folders. When `search` is set, results span the whole team (not just the
    current folder).
    """
    if team == "all":
        team = None
    if not entity_name:
        if team:
            entity_name = get_home_folder(team)["name"]
        else:
            frappe.throw("You must provide a folder to query", ValueError)

    entity = frappe.get_doc("File", entity_name)
    team = entity.team

    if not user_has_permission(entity, "read"):
        frappe.throw(
            f"You don't have access.",
            frappe.exceptions.PermissionError,
        )

    if is_site_file(entity):
        # Framework folder (e.g. desk "Home"): list via frappe.get_list so the
        # framework's own File permissions apply. team dropped so get_query_data
        # skips the Drive-only team filter.
        ff_filters = {"folder": entity_name}
        if search:
            ff_filters["file_name"] = ["like", f"%{search}%"]
        names = frappe.get_list("File", filters=ff_filters, pluck="name")
        return get_query_data(
            frappe.qb.from_(DriveFile).where(DriveFile.name.isin(names or [""])),
            file_kinds=file_kinds,
            order_by=order_by,
            ascending=ascending,
            start=start,
            limit=limit,
        )

    # Folder browse isn't user-scoped, so restrict to team files (Site files use the ff branch).
    query = _get_basic_query(search).where(DriveFile.team.isnotnull())
    if search:
        if not team:
            query = query.where(DriveFile.team.isin(get_teams() or [""]))
    else:
        # Folder browsing; search is team-wide so it skips the folder filter.
        query = query.where(DriveFile.folder == entity_name)

    return get_query_data(
        query,
        team=team,
        file_kinds=file_kinds,
        entity_name=entity_name,
        order_by=order_by,
        ascending=ascending,
        start=start,
        limit=limit,
    )

@frappe.whitelist()
@default_team
def shared(
    team: str,
    shared_type: str = "with",
    order_by: str = "modified",
    ascending: bool = True,
    file_kinds: list[str] | str = [],
    search: str = None,
):
    """
    Returns shared files based on shared_type parameter.
    - "with": files shared with current user
    - "public": publicly shared files
    """
    query = _get_basic_query(search)

    return get_query_data(
        query,
        shared_type=shared_type,
        file_kinds=file_kinds,
        team=team,
        order_by=order_by,
        ascending=ascending,
    )


@frappe.whitelist()
@default_team
def favourites(
    team: str,
    order_by: str = "modified",
    ascending: bool = True,
    file_kinds: list[str] | str = [],
    search: str = None,
):
    """
    Returns all files marked as favourite by the current user.
    """
    query = _get_basic_query(search)

    return get_query_data(
        query,
        favourites_only=True,
        file_kinds=file_kinds,
        team=team,
        order_by=order_by,
        ascending=ascending,
    )


@frappe.whitelist()
@default_team
def recents(
    team: str,
    order_by: str = "modified",
    ascending: bool = True,
    file_kinds: list[str] | str = [],
    search: str = None,
):
    """
    Returns all files marked recently by the current user.
    """
    query = _get_basic_query(search)

    return get_query_data(
        query,
        recents_only=True,
        file_kinds=file_kinds,
        team=team,
        order_by=order_by,
        ascending=ascending,
    )


@frappe.whitelist()
@default_team
def trash(
    team: str,
    order_by: str = "modified",
    ascending: bool = True,
    file_kinds: list[str] | str = [],
    search: str = None,
):
    """
    Returns all deleted files (trash) for the current user.
    """
    query = (
        frappe.qb.from_(DriveFile)
        .where(DriveFile.status == STATUS_TRASHED)
        .where(DriveFile.team.isnotnull())
        .where(DriveFile.owner == frappe.session.user)
    )
    if search:
        query = query.where(DriveFile.file_name.like(f"%{search}%"))

    return get_query_data(
        query,
        team=team,
        file_kinds=file_kinds,
        order_by=order_by,
        ascending=ascending,
    )


ALLOWED_SORT_FIELDS = {
    "name", "file_name", "file_size", "file_type", "creation", "modified", "owner",
}


def get_query_data(
    query,
    favourites_only=False,
    recents_only=False,
    file_kinds=[],
    team=None,
    entity_name=None,
    shared_type=None,
    order_by="modified",
    ascending=True,
    start=0,
    limit=None,
):
    """
    Runs all the necessary commands to obtain files in the structure expected by Drive frontend.
    """
    if order_by not in ALLOWED_SORT_FIELDS:
        order_by = "modified"

    # Filter by team
    if team and team != "all":
        query = query.where(DriveFile.team == team)

    # Apply shared filter
    query = _apply_shared_filter(query, shared_type)
    query = query.select(
        *FILE_FIELDS,
        DrivePermission.user.as_("shared_team"),
    ).where(fn.Coalesce(DrivePermission.read, 1).as_("read") == 1)

    # Send owner display data with files so the list view doesn't need a separate users fetch
    query = query.left_join(DriveUser).on(DriveUser.name == DriveFile.owner).select(
        DriveUser.full_name.as_("owner_full_name"), DriveUser.user_image.as_("owner_image")
    )

    # Apply favourites filter
    if favourites_only:
        query = query.right_join(DriveFavourite)
    else:
        query = query.left_join(DriveFavourite)

    query = query.on((DriveFavourite.entity == DriveFile.name) & (DriveFavourite.user == frappe.session.user)).select(
        DriveFavourite.name.as_("is_favourite")
    )

    # Apply recents filter
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
            .orderby(DriveFile[order_by], order=Order.asc if ascending else Order.desc)
        )

    query = query.select(Recents.last_interaction.as_("accessed"))

    # Apply file kind filter
    query = _apply_file_kinds_filter(query, file_kinds)

    # Page through large result sets (aggregation below is scoped to the page).
    if limit:
        query = query.limit(int(limit)).offset(int(start or 0))

    res = query.run(as_dict=True)

    default = get_default_access(entity_name) if entity_name else 0

    # Deduplicate results
    if shared_type:
        added = set()
        filtered_list = []
        for r in res:
            if r["name"] not in added:
                filtered_list.append(r)
            added.add(r["name"])
        res = filtered_list

    # Get aggregated data, scoped to the files we're returning
    names = [r["name"] for r in res]
    children_count = _get_children_count(res)
    share_count = _get_share_count(names)
    public_files = _get_public_files(names)
    team_files = _get_team_files(names)

    # Enrich results with aggregated data and permissions
    for r in res:
        name = r["name"]
        r["child_count"] = children_count.get(name, 0)
        if name in public_files:
            r["share_count"] = -2
        elif default > -1 and name in team_files:
            r["share_count"] = -1
        elif default == 0:
            r["share_count"] = share_count.get(name, default)
        else:
            r["share_count"] = default

        if is_site_file(r):
            r["file_type"] = map_ff_to_drive_type(r)
        r["kind"] = entity_kind(r)
        hide_storage_key(r)
        r |= get_user_access(name)

    return res


@frappe.whitelist()
def get_attachments(doctype: str | None = None, docname: str | None = None):
    """
    Returns all files that are attached to a document.
    If either doctype or docname isn't specified, returns a list of folder-like objects
    that represents the tree Doctype > Doc > Attachments.
    """
    if doctype and docname:
        files = frappe.get_list(
            "File", filters={"attached_to_doctype": doctype, "attached_to_name": docname}, pluck="name"
        )
        query = frappe.qb.from_(DriveFile).where(DriveFile.name.isin(files))
        return get_query_data(query)

    titles = {}
    if doctype:
        names = frappe.get_list("File", filters={"attached_to_doctype": doctype}, fields=["attached_to_name"])
        doctypes_set = Counter(k["attached_to_name"] for k in names)
        # Show each document by its title field rather than its raw name (ID).
        title_field = frappe.get_meta(doctype).get_title_field()
        if title_field != "name":
            titles = dict(
                frappe.get_all(
                    doctype,
                    filters={"name": ["in", list(doctypes_set)]},
                    fields=["name", title_field],
                    as_list=True,
                )
            )
    else:
        doctypes = frappe.get_list(
            "File", filters={"attached_to_doctype": ["is", "set"]}, fields=["attached_to_doctype"]
        )
        doctypes_set = Counter(k["attached_to_doctype"] for k in doctypes)

    return [
        {
            "name": name,
            "file_name": titles.get(name) or name,
            "is_folder": 1,
            "file_type": "Folder",
            "child_count": size,
            "kind": KIND_VIRTUAL,
            "attached_to_doctype": doctype or name,
            "attached_to_name": name if doctype else None,
        }
        for name, size in doctypes_set.items()
    ]
