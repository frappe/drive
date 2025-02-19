import frappe
from frappe.utils import getdate

from drive.utils.users import mark_as_viewed
from drive.utils.files import get_valid_breadcrumbs


ENTITY_FIELDS = [
    "name",
    "title",
    "is_group",
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
        entity = frappe.get_doc("Drive File", entity)
    fields = ["read", "comment", "write", "share", "name as permission_name", "valid_until"]
    NO_ACCESS = {
        "read": 0,
        "comment": 0,
        "share": 0,
        "write": 0,
    }

    # If unauthorized
    if not user or user == "Guest":
        public_access = frappe.db.get_value(
            "Drive Permission",
            {"entity": entity.name, "user": ""},
            fields,
            as_dict=1,
        )
        if public_access:
            return public_access
        return NO_ACCESS

    # If logged in, first get Permission
    user_access = (
        frappe.db.get_value(
            "Drive Permission",
            {
                "entity": entity.name,
                "user": user,
            },
            fields,
            as_dict=1,
        )
        or {}
    )

    # Otherwise, check team/admin/owner
    teams = get_teams(user)
    other_access = {}
    if user == entity.owner:
        other_access = {"read": 1, "comment": 1, "share": 1, "write": 1, "type": "admin"}
    elif entity.team in teams:
        # Allow write access for uploading to home folder
        if not entity.parent_entity:
            other_access = {"read": 1, "comment": 1, "share": 1, "write": 1, "type": "team"}
        else:
            other_access = {"read": 1, "comment": 1, "share": 1, "write": 0, "type": "team"}

    return {**other_access, **user_access}


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
    user_access = get_user_access(entity, frappe.session.user)
    if user_access.get("read") == 0:
        frappe.throw("Not found", frappe.NotFound)

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
    return_obj = entity | user_access | owner_info | breadcrumbs | {"is_favourite": favourite}
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
def get_shared_with_list(entity_name):
    """
    Return the list of users with whom this file or folder has been shared

    :param entity_name: Document-name of this file or folder
    :raises PermissionError: If the user does not have edit permissions
    :return: List of users, with permissions and last modified datetime
    :rtype: list[frappe._dict]
    """
    if not frappe.has_permission(
        doctype="Drive File", doc=entity_name, ptype="share", user=frappe.session.user
    ):
        raise frappe.PermissionError
    permissions = frappe.db.get_all(
        "Drive Permission",
        filters={"entity": entity_name, "user": ["!=", ""]},
        order_by="user",
        fields=["user", "read", "write", "comment", "share"],
    )

    for p in permissions:
        user_info = frappe.db.get_value(
            "User", p.user, ["user_image", "full_name", "email"], as_dict=True
        )
        p.update(user_info)
    return permissions


# BROKEN
@frappe.whitelist()
def update_document_invalidation(entity_name, invalidation_date):
    x = frappe.get_list(
        "Drive DocShare",
        filters={"share_name": entity_name, "share_doctype": "Drive File"},
        order_by="creation desc",
        fields=["name", "valid_until", "share_parent"],
    )
    for i in x:
        doc = frappe.get_doc("Drive DocShare", i.name)
        doc.valid_until = invalidation_date
        doc.save()


def auto_delete_expired_docshares():
    current_date = getdate()
    expired_documents = frappe.get_list(
        "Drive Permission",
        filters=[
            ["valid_until", "<", current_date],
            ["valid_until", "is", "set"],
        ],
        order_by="creation desc",
        fields=["name", "valid_until"],
    )
    if expired_documents:

        def batch_delete_perms(docs):
            for d in docs:
                frappe.delete_doc("Drive Permission", d.name)

        frappe.enqueue(batch_delete_perms, docs=expired_documents)
    return


def user_has_permission(doc, ptype, user):
    if doc.owner == user or user == "Administrator":
        return True
    access = get_user_access(doc, user)
    if ptype in access:
        return access[ptype]
