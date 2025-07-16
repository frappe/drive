import frappe
from frappe.utils import getdate

from drive.utils.users import mark_as_viewed
from drive.utils.files import get_valid_breadcrumbs, generate_upward_path, get_file_type


ENTITY_FIELDS = [
    "name",
    "title",
    "is_group",
    "is_link",
    "path",
    "modified",
    "creation",
    "file_size",
    "mime_type",
    "color",
    "document",
    "owner",
    "parent_entity",
    "is_private",
]


@frappe.whitelist(allow_guest=True)
def get_user_access(entity, user=frappe.session.user):
    """
    Return the user specific access permissions for an entity if it exists or general access permissions

    :param entity_name: Document-name of the entity whose permissions are to be fetched
    :return: Dict of general access permissions (read, write)
    :rtype: frappe._dict or None
    """
    if isinstance(entity, str):
        entity = frappe.get_cached_doc("Drive File", entity)
    print(user, entity.owner)
    if user == entity.owner:
        return {"read": 1, "comment": 1, "share": 1, "upload": 1, "write": 1, "type": "admin"}

    # Default access based on public or team view
    teams = get_teams(user)
    access = get_access(entity.team)
    if entity.team in teams and entity.is_private == 0:
        # Everyone can upload to team folders, and admins can edit all files
        access = {
            "read": 1,
            "comment": 1,
            "share": 1,
            "upload": int(entity.is_group),
            "write": int(access == 2 or entity.owner == user),
            "type": {2: "team-admin", 1: "team", 0: "guest"}[access],
        }
    else:
        access = {
            "read": 0,
            "comment": 0,
            "share": 0,
            "write": 0,
            "upload": 0,
        }

    path = generate_upward_path(entity.name, user)
    user_access = {k: v for k, v in path[-1].items() if k in access.keys()}
    if not user or user == "Guest":
        return user_access

    public_path = generate_upward_path(entity.name, "Guest")
    public_access = {k: v for k, v in public_path[-1].items() if k in access.keys()}

    valid_accesses = [user_access, public_access]
    if entity.team in teams:
        team_path = generate_upward_path(entity.name, "$TEAM")
        team_access = {k: v for k, v in team_path[-1].items() if k in access.keys()}
        valid_accesses.append(team_access)
    for access_type in valid_accesses:
        for type, v in access_type.items():
            if v:
                access[type] = 1

    return access


@frappe.whitelist()
def is_admin(team):
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[frappe.session.user].access_level == 2


def get_access(team):
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[frappe.session.user].access_level


@frappe.whitelist()
def get_teams(user=None, details=None):
    """
    Returns all the teams that the current user is part of.
    """
    if not user:
        user = frappe.session.user
    teams = frappe.get_all(
        "Drive Team Member",
        pluck="parent",
        filters=[
            ["parenttype", "=", "Drive Team"],
            ["user", "=", user],
        ],
    )
    if details:
        return {team: frappe.get_doc("Drive Team", team) for team in teams}

    return teams


@frappe.whitelist(allow_guest=True)
def get_entity_with_permissions(entity_name):
    """
    Return file data with permissions

    :param entity_name: Name of file document.
    :raises IsADirectoryError: If this DriveEntity doc is not a file
    :return: DriveEntity with permissions
    :rtype: frappe._dict
    """
    entity = frappe.db.get_value(
        "Drive File", {"is_active": 1, "name": entity_name}, ENTITY_FIELDS + ["team"], as_dict=1
    )
    if not entity:
        frappe.throw("We couldn't find what you're looking for.", {"error": frappe.NotFound})

    user_access = get_user_access(entity, frappe.session.user)
    if user_access.get("read") == 0:
        frappe.throw("You don't have access to this file.", {"error": frappe.PermissionError})

    owner_info = (
        frappe.db.get_value("User", entity.owner, ["user_image", "full_name"], as_dict=True) or {}
    )
    breadcrumbs = {"breadcrumbs": get_valid_breadcrumbs(entity, user_access)}
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
    entity_doc_content = (
        frappe.db.get_value(
            "Drive Document",
            entity.document,
            ["content", "raw_content", "settings", "version"],
            as_dict=1,
        )
        or {}
    )
    return return_obj | entity_doc_content


@frappe.whitelist()
def get_shared_with_list(entity):
    """
    Return the list of users with whom this file or folder has been shared

    :param entity: Document-name of this file or folder
    :raises PermissionError: If the user does not have edit permissions
    :return: List of users, with permissions and last modified datetime
    :rtype: list[frappe._dict]
    """
    if not frappe.has_permission(
        doctype="Drive File", doc=entity, ptype="share", user=frappe.session.user
    ):
        raise frappe.PermissionError
    permissions = frappe.db.get_all(
        "Drive Permission",
        filters=[["entity", "=", entity], ["user", "!=", ""], ["user", "!=", "$TEAM"]],
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


def user_has_permission(doc, ptype, user):
    if doc.owner == user or user == "Administrator":
        return True
    access = get_user_access(doc, user)
    if ptype in access:
        return access[ptype]
