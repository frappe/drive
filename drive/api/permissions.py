import frappe
from frappe.utils import getdate

from drive.utils.users import mark_as_viewed
from drive.utils.files import get_valid_breadcrumbs, generate_upward_path


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
        entity = frappe.get_doc("Drive File", entity)

    if user == entity.owner:
        return {"read": 1, "comment": 1, "share": 1, "write": 1, "type": "admin"}

    # Default access based on public or team view
    teams = get_teams(user)
    if entity.team in teams and not entity.is_private:
        # Everyone can upload to team folders
        access = {
            "read": 1,
            "comment": 1,
            "share": 1,
            "write": 1 if entity.is_group else 0,
            "type": "team",
        }
    else:
        access = {
            "read": 0,
            "comment": 0,
            "share": 0,
            "write": 0,
        }

    path = generate_upward_path(entity.name, user)

    user_access = {k: v for k, v in path[-1].items() if k in access.keys()}
    if user == "Guest":
        return user_access

    public_path = generate_upward_path(entity.name, "Guest")
    public_access = {k: v for k, v in public_path[-1].items() if k in access.keys()}
    for access_type in (user_access, public_access):
        for type, v in access_type.items():
            if v:
                access[type] = 1

    return access


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
        frappe.throw("We couldn't find what you're looking for.", {"error": frappe.NotFound})

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
    print(user_access)
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
    Return the list of active users with whom this file or folder has been shared
    """
    if not frappe.has_permission(
        doctype="Drive File", doc=entity_name, ptype="share", user=frappe.session.user
    ):
        raise frappe.PermissionError
    
    # Modified query to filter active, non-deleted users
    permissions = frappe.db.get_all(
        "Drive Permission",
        filters={
            "entity": entity_name, 
            "user": ["!=", ""],
            # Join with User table to check status
            "user.enabled": 1,
            "user.deleted": 0
        },
        order_by="user",
        fields=["user", "read", "write", "comment", "share"],
    )

    # Additional check for user status
    valid_permissions = []
    for p in permissions:
        user_status = frappe.db.get_value("User", p.user, ["enabled", "deleted"], as_dict=True)
        if user_status and user_status.enabled and not user_status.deleted:
            user_info = frappe.db.get_value(
                "User", 
                p.user, 
                ["user_image", "full_name", "email"], 
                as_dict=True
            )
            p.update(user_info)
            valid_permissions.append(p)
    
    return valid_permissions


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

@frappe.whitelist()
def cleanup_deleted_user_permissions():
    """
    Remove permissions for deleted users
    """
    # Get all permissions where user exists but is deleted/disabled
    invalid_permissions = frappe.db.sql("""
        SELECT dp.name 
        FROM `tabDrive Permission` dp
        LEFT JOIN `tabUser` u ON dp.user = u.name
        WHERE dp.user != '' 
        AND (u.name IS NULL OR u.enabled = 0 OR u.deleted = 1)
    """, as_dict=True)
    
    # Delete them in batches
    for perm in invalid_permissions:
        frappe.delete_doc("Drive Permission", perm.name)
    
    return {"count": len(invalid_permissions)}

def validate_write_permission(entity_name, user=None):
    """
    Explicit permission check for write operations like rename
    """
    if not user:
        user = frappe.session.user
    
    entity = frappe.get_doc("Drive File", entity_name)
    access = get_user_access(entity, user)
    
    if not access.get("write"):
        frappe.throw(
            "You don't have permission to rename this item",
            frappe.PermissionError
        )
    
    # Additional check for duplicate name in parent folder
    if entity.parent_entity:
        siblings = frappe.get_all(
            "Drive File",
            filters={
                "parent_entity": entity.parent_entity,
                "name": ("!=", entity_name),
                "is_active": 1
            },
            pluck="name"
        )
        # This will help the rename function catch duplicates early
        return {
            "has_permission": True,
            "sibling_names": siblings
        }
    return {"has_permission": True}