import frappe
from frappe.utils import getdate
from frappe.model.document import Document
from frappe.core.doctype.file.file import has_permission as ff_has_permission

from drive.utils import (
    generate_upward_path,
    get_default_team,
    get_valid_breadcrumbs,
    FILE_FIELDS,
    get_home_folder,
    map_ff_to_drive_type,
    STATUS_ACTIVE,
)


NO_ACCESS = {
    "read": 0,
    "comment": 0,
    "share": 0,
    "write": 0,
    "upload": 0,
}


def filter_access(path):
    return {k: v for k, v in path[-1].items() if k in NO_ACCESS.keys()}


def get_team_access(entity):
    path = generate_upward_path(entity.name, team=1)
    return {**filter_access(path), "team": path[-1]["shared_team"]}


@frappe.whitelist(allow_guest=True)
def get_user_access(entity: str | Document | frappe._dict, user: str = None, team: bool = False):
    """
    Return the user specific permissions for an entity. Toggle `team` to check team permission.
    """
    if isinstance(entity, str):
        entity = frappe.get_cached_doc("File", entity)

    access = NO_ACCESS.copy()
    if not user:
        if team:
            # Return team perms immediately
            return get_team_access(entity)
        else:
            user = frappe.session.user
    # if not team and user not in [frappe.session.user, "Guest"] and not is_admin(entity.team):
    #     frappe.throw("You cannot check permissions of other users", PermissionError)

    # Owners and team members of a file have access
    teams = get_teams(user)

    if frappe.db.get_value("Drive Team", entity.team, "public"):
        access["read"] = 1

    if user == entity.owner:
        access = {"read": 1, "comment": 1, "share": 1, "upload": 1, "write": 1, "type": "admin"}
    elif entity.team in teams:
        access_level = get_access_level(entity.team, user)
        access = {
            "read": 1,
            "comment": 1,
            "share": 0,
            "upload": int(entity.is_folder) and access_level,
            "write": int(access_level == 2 or entity.owner == user),
            "type": {2: "admin", 1: "user", 0: "guest"}[access_level],
        }
    path = generate_upward_path(entity.name, user)

    # Public access
    user_access = {k: v for k, v in path[-1].items() if k in access.keys()}
    if user == "Guest":
        # Special for public teams
        if access["read"]:
            user_access["read"] = 1
        return user_access

    # Gather all accesses, and award highest
    public_access = filter_access(generate_upward_path(entity.name, "Guest"))
    team_access = get_team_access(entity)
    if team_access["team"] not in teams:
        team_access = NO_ACCESS

    for access_type in [user_access, team_access, public_access]:
        for type_, v in access_type.items():
            if v:
                access[type_] = 1

    return access


@frappe.whitelist()
def is_admin(team: str):
    if frappe.session.user == "Administrator":
        return True
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[frappe.session.user].access_level == 2


def get_access_level(team, user=None):
    if not user:
        user = frappe.session.user
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[user].access_level


@frappe.whitelist()
def get_teams(user: str = None, details: bool = False, exclude_personal: bool = True):
    """
    Returns all the teams that the current user is part of.
    """
    if not user:
        user = frappe.session.user

    teams = frappe.get_all(
        "Drive Team Member",
        pluck="parent",
        filters=[["parenttype", "=", "Drive Team"], ["user", "=", user]],
    )
    if details:
        teams_info = {
            team: {**frappe.get_doc("Drive Team", team).as_dict(), "file": get_home_folder(team)["name"]}
            for team in teams
        }
        if exclude_personal:
            return {t: team for t, team in teams_info.items() if not team["personal"]}
        return teams_info
    return teams


@frappe.whitelist(allow_guest=True)
def get_public_teams():
    return frappe.get_all("Drive Team", fields=["name", "title"], filters=[["public", "=", 1]])


@frappe.whitelist(allow_guest=True)
def get_entity_with_permissions(entity_name: str):
    """
    Return file data with permissions
    """
    entity = frappe.get_all(
        "File",
        filters={"name": entity_name},
        or_filters={"status": STATUS_ACTIVE, "is_drive_file": 0},
        fields=FILE_FIELDS,
        limit=1,
    )
    if not entity:
        # Mimic API v2 points
        frappe.local.response.errors = [
            {
                "type": "PageDoesNotExistError",
                "message": "We couldn't find what you're looking for.",
            }
        ]
        frappe.throw("We couldn't find what you're looking for.", frappe.PageDoesNotExistError)
    entity = entity[0]

    entity["in_home"] = entity.team == get_default_team()
    user_access = get_user_access(entity)
    if not user_access.get("read"):
        frappe.local.response.errors = [
            {
                "type": "PermissionError",
                "message": "You don't have access to this file.",
            }
        ]
        frappe.throw("You don't have access to this file.", frappe.PermissionError)

    owner_info = frappe.db.get_value("User", entity.owner, ["user_image", "full_name"], as_dict=True) or {}
    breadcrumbs = {"breadcrumbs": get_valid_breadcrumbs(entity.name, user_access)}
    favourite = frappe.db.get_value(
        "Drive Favourite",
        {
            "entity": entity_name,
            "user": frappe.session.user,
        },
        ["entity as is_favourite"],
    )
    return_obj = entity | user_access | owner_info | breadcrumbs | {"is_favourite": favourite}

    default = 0
    if entity_name:
        if get_user_access(entity_name, "Guest")["read"]:
            default = -2
        elif get_user_access(entity_name, team=1)["read"]:
            default = -1
    return_obj["share_count"] = default
    if not entity.is_drive_file:
        return_obj["file_type"] = map_ff_to_drive_type(entity)

    return_obj["modifiable"] = entity["is_drive_file"] and not entity["content_doctype"] == "File"
    return_obj["is_attachment"] = entity["is_drive_file"] and entity["content_doctype"] == "File"

    # To work with modern frappe-ui composables
    frappe.response["data"] = return_obj
    return return_obj


@frappe.whitelist()
def get_shared_with_list(entity: str):
    """
    Return the list of users with whom this file or folder has been shared

    :param entity: Document-name of this file or folder
    :raises PermissionError: If the user does not have edit permissions
    :return: List of users, with permissions and last modified datetime
    :rtype: list[frappe._dict]
    """
    if not user_has_permission(entity, "share"):
        raise frappe.PermissionError("You do not have permission to check the shares.")

    permissions = frappe.db.get_all(
        "Drive Permission",
        filters=[["entity", "=", entity], ["user", "!=", ""], ["team", "!=", "1"]],
        order_by="user",
        fields=["user", "read", "write", "comment", "upload", "share"],
    )

    owner = frappe.db.get_value("File", entity, "owner")
    permissions.insert(
        0,
        frappe.db.get_value("User", owner, ["user_image", "full_name", "name as user"], as_dict=True),
    )

    for p in permissions:
        user_info = frappe.db.get_value("User", p.user, ["user_image", "full_name", "email"], as_dict=True)
        if user_info:
            p.update(user_info)
    return permissions


def user_has_permission(doc, ptype, user=None, team=0):
    if isinstance(doc, str):
        doc = frappe.get_doc("File", doc)
    if not doc.is_drive_file:
        return ff_has_permission(doc, ptype, user)

    if not user:
        user = frappe.session.user
    if user == "Administrator" or ptype == "create":
        return True
    if ptype not in ("read", "write", "comment", "share", "upload"):
        # Should ideally deflect to Framework
        ptype = "write"
    access = get_user_access(doc, user, team)
    if ptype in access:
        return bool(access[ptype])
