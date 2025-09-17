import io

import frappe
import markdown
from frappe.utils import getdate
from markdown.extensions.wikilinks import WikiLinkExtension
from pypika import Field

from drive.utils import (
    generate_upward_path,
    get_default_team,
    get_file_type,
    get_valid_breadcrumbs,
)
from drive.utils.files import FileManager
from drive.utils.users import mark_as_viewed

ENTITY_FIELDS = [
    "name",
    "title",
    "is_group",
    "is_link",
    "path",
    Field("_modified").as_("modified"),
    "creation",
    "file_size",
    "mime_type",
    "color",
    "document",
    "owner",
    "parent_entity",
]


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
def get_user_access(entity, user: str = None, team: bool = False):
    """
    Return the user specific permissions for an entity. Toggle `team` to check team permission.
    """
    if isinstance(entity, str):
        entity = frappe.get_cached_doc("Drive File", entity)

    access = NO_ACCESS.copy()
    # Return team perms immediately
    if not user:
        if team:
            return get_team_access(entity)
        else:
            user = frappe.session.user
    if user not in [frappe.session.user, "Guest"] and not is_admin(entity.team):
        frappe.throw("You cannot check permissions of other users", PermissionError)

    # Owners and team members of a file have access
    teams = get_teams(user)

    if user == entity.owner:
        access = {"read": 1, "comment": 1, "share": 1, "upload": 1, "write": 1, "type": "admin"}
    elif entity.team in teams:
        access_level = get_access_level(entity.team)
        access = {
            "read": 1,
            "comment": 1,
            "share": 1,
            "upload": int(entity.is_group),
            "write": int(access_level == 2 or entity.owner == user),
            "type": {2: "admin", 1: "user", 0: "guest"}[access_level],
        }
    path = generate_upward_path(entity.name, user)

    # Public access
    user_access = {k: v for k, v in path[-1].items() if k in access.keys()}
    if user == "Guest":
        # broken: leaks parent breadcrumbs
        return user_access

    # Gather all accesses, and award highest
    public_access = filter_access(generate_upward_path(entity.name, "Guest"))
    team_access = get_team_access(entity)
    if team_access["team"] not in teams:
        team_access = NO_ACCESS

    for access_type in [user_access, team_access, public_access]:
        for type, v in access_type.items():
            if v:
                access[type] = 1

    if not access["read"]:
        frappe.throw("You cannot check permissions unless you can read the file.", PermissionError)
    return access


@frappe.whitelist()
def is_admin(team):
    if frappe.session.user == "Administrator":
        return True
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[frappe.session.user].access_level == 2


def get_access_level(team):
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[frappe.session.user].access_level


@frappe.whitelist()
def get_teams(user=None, details=None, exclude_personal=True):
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
        teams_info = {team: frappe.get_doc("Drive Team", team) for team in teams}
        if exclude_personal:
            return {t: team for t, team in teams_info.items() if not team.personal}
    return teams


@frappe.whitelist(allow_guest=True)
def get_entity_with_permissions(entity_name):
    """
    Return file data with permissions
    """
    entity = frappe.db.get_value(
        "Drive File",
        {"is_active": 1, "name": entity_name},
        ENTITY_FIELDS + ["team"],
        as_dict=1,
    )
    if not entity:
        frappe.throw("We couldn't find what you're looking for.", {"error": frappe.NotFound})

    entity["in_home"] = entity.team == get_default_team()
    user_access = get_user_access(entity)
    if user_access.get("read") == 0:
        frappe.throw("You don't have access to this file.", {"error": frappe.PermissionError})

    owner_info = (
        frappe.db.get_value("User", entity.owner, ["user_image", "full_name"], as_dict=True) or {}
    )
    breadcrumbs = {"breadcrumbs": get_valid_breadcrumbs(entity.name, user_access)}
    favourite = frappe.db.get_value(
        "Drive Favourite",
        {
            "entity": entity_name,
            "user": frappe.session.user,
        },
        ["entity as is_favourite"],
    )
    mark_as_viewed(entity)
    file_type = get_file_type(entity)
    return_obj = (
        entity
        | user_access
        | owner_info
        | breadcrumbs
        | {"is_favourite": favourite, "file_type": file_type}
    )
    if entity.mime_type == "text/markdown":
        entity.document_type == "markdown"
        manager = FileManager()
        wrapper = io.TextIOWrapper(manager.get_file(entity.path))
        url_builder = (
            lambda label, base, end: f"/api/method/drive.api.docs.get_wiki_link?team={entity.team}&title={label}"
        )
        with wrapper as r:
            content = r.read()
            return_obj["raw_content"] = markdown.markdown(
                content,
                output_format="html",
                extensions=["extra", WikiLinkExtension(build_url=url_builder)],
            )

    if entity.document:
        k = frappe.get_doc("Drive Document", entity.document)
        entity_doc_content = k.as_dict()
        entity_doc_content.pop("name")
        comments = frappe.get_all(
            "Drive Comment",
            filters={"parenttype": "Drive File", "parent": entity.name},
            fields=["content", "owner", "creation", "name", "resolved"],
        )

        for k in comments:
            k["replies"] = frappe.get_all(
                "Drive Comment",
                filters={"parenttype": "Drive Comment", "parent": k["name"]},
                fields=["content", "owner", "creation", "name"],
            )

        return_obj |= entity_doc_content | {"comments": comments, "modified": entity.modified}
    return return_obj


@frappe.whitelist()
def get_shared_with_list(entity):
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

    owner = frappe.db.get_value("Drive File", entity, "owner")
    permissions.insert(
        0,
        frappe.db.get_value(
            "User", owner, ["user_image", "full_name", "name as user"], as_dict=True
        ),
    )

    for p in permissions:
        user_info = frappe.db.get_value(
            "User", p.user, ["user_image", "full_name", "email"], as_dict=True
        )
        p.update(user_info)
    return permissions


def auto_delete_expired_perms():
    current_date = getdate()
    expired_documents = frappe.get_list(
        "Drive Permission",
        filters=[
            ["valid_until", "is", "set"],
            ["valid_until", "<", current_date],
        ],
        fields=["name", "valid_until"],
    )
    if expired_documents:

        def batch_delete_perms(docs):
            for d in docs:
                frappe.delete_doc("Drive Permission", d.name)

        frappe.enqueue(batch_delete_perms, docs=expired_documents)


def user_has_permission(doc, ptype, user=None):
    if not user:
        user = frappe.session.user
    if user == "Administrator" or ptype == "create":
        return True
    if "ptype" not in ("read", "write", "comment", "share", "upload"):
        # Should ideally deflect to Framework
        ptype = "write"
    access = get_user_access(doc, user)
    if ptype in access:
        return bool(access[ptype])


def user_has_permission_doc(doc, ptype, user=None):
    return user_has_permission(
        frappe.get_value("Drive File", {"document": doc.name}, "name"), ptype, user
    )
