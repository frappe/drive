import frappe
from frappe.utils import getdate
from pypika import Order, Case, functions as fn

from drive.utils.users import mark_as_viewed
from drive.api.files import (
    generate_upward_path,
    get_ancestors_of,
    get_user_directory,
    get_doc_content,
)


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
]


def get_teams(user=None):
    """
    Returns all the teams that the current user is part of.
    """
    if not user:
        user = frappe.session.user
    return frappe.get_all(
        "Drive Team Member",
        pluck="parent",
        filters=[
            ["parenttype", "=", "Drive Team"],
            ["user", "=", user],
        ],
    )


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
        "Drive Entity", {"is_active": 1, "name": entity_name}, ENTITY_FIELDS + ["team"], as_dict=1
    )
    user_access = get_user_access(entity)
    if user_access.get("read") == 0:
        frappe.throw("Not found", frappe.NotFound)

    owner_info = frappe.db.get_value(
        "User", entity.owner, ["user_image", "full_name"], as_dict=True
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

    if entity.document:
        entity_doc_content = get_doc_content(entity.document)
        return_obj = return_obj | entity_doc_content
    return return_obj


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
        doctype="Drive Entity", doc=entity_name, ptype="write", user=frappe.session.user
    ):
        raise frappe.PermissionError

    entity_owner = frappe.db.get_value("Drive Entity", entity_name, "owner")

    users = frappe.db.get_all(
        "Drive DocShare",
        filters={
            "share_doctype": "Drive Entity",
            "share_name": entity_name,
            "user_doctype": "User",
            "user_name": ["not in", [frappe.session.user, entity_owner]],
            "everyone": 0,
            "public": 0,
            "protected": 0,
        },
        order_by="name",
        fields=["user_name", "read", "write", "share"],
    )

    entity_owner_info = frappe.db.get_value(
        "User", entity_owner, ["user_image", "full_name", "email"], as_dict=True
    )
    for user in users:
        user_info = frappe.db.get_value(
            "User", user.user_name, ["user_image", "full_name"], as_dict=True
        )
        user.update(user_info)
    return {"owner": entity_owner_info, "users": users}


@frappe.whitelist()
def get_shared_user_group_list(entity_name):
    user_group_list = frappe.db.get_list(
        "Drive DocShare",
        filters={
            "share_doctype": "Drive Entity",
            "user_doctype": "User Group",
            "share_name": ["like", f"%{entity_name}%"],
        },
        fields=["user_name", "user_doctype", "read", "write"],
    )
    return user_group_list


@frappe.whitelist()
def get_shared_by_me(get_all=False, order_by="modified", is_active=1, limit=100, offset=0):
    """
    Return the list of files and folders shared with the current user

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """

    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    DriveUser = frappe.qb.DocType("User")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveUser.full_name,
        DriveUser.user_image,
        DriveEntity.owner,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_comments,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.allow_download,
        DriveDocShare.read,
        DriveDocShare.write,
        DriveDocShare.everyone,
        DriveDocShare.share,
        DriveDocShare.owner_parent,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .left_join(DriveDocShare)
        .on(
            (DriveDocShare.share_name == DriveEntity.name)
            & (DriveEntity.owner == frappe.session.user)
        )
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .left_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
        .where(
            (DriveEntity.is_active == 1)
            & (
                (DriveDocShare.user_name != frappe.session.user)
                | (DriveDocShare.everyone == 1)
                | (DriveDocShare.public == 1)
            )
            & (DriveDocShare.owner_parent.isnull())
        )
        .groupby(DriveEntity.name)
        .orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    if get_all:
        return query.run(as_dict=True)

    return query.run(as_dict=True)


@frappe.whitelist()
def get_shared_with_me(get_all=False, order_by="modified", is_active=1, limit=100, offset=0):
    """
    Return the list of files and folders shared with the current user

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """

    DocShare = frappe.qb.DocType("Drive DocShare")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
    UserGroupMember = frappe.qb.DocType("User Group Member")
    DriveUser = frappe.qb.DocType("User")
    selectedFields = [
        DriveEntity.name,
        DriveEntity.title,
        DriveEntity.is_group,
        DriveEntity.owner,
        DriveUser.full_name,
        DriveUser.user_image,
        DriveEntity.modified,
        DriveEntity.creation,
        DriveEntity.file_size,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_comments,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.allow_download,
        DocShare.read,
        fn.Max(DocShare.write).as_("write"),
        DocShare.everyone,
        DocShare.share,
        DocShare.share_parent,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .inner_join(DocShare)
        .on((DocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on((UserGroupMember.parent == DocShare.user_name))
        .left_join(DriveFavourite)
        .on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
        .where(
            (DriveEntity.is_active == 1)
            & (
                (UserGroupMember.user == frappe.session.user)
                | ((DocShare.user_name == frappe.session.user) | (DocShare.everyone == 1))
            )
            & (DocShare.share_parent.isnull())
            & (DriveEntity.owner != frappe.session.user)
        )
        .groupby(DriveEntity.name)
        .orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
        .orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )
    )
    if get_all:
        return query.run(as_dict=True)

    return query.run(as_dict=True)


@frappe.whitelist()
def get_all_my_entities(fields=None):
    """
    Return file data with permissions

    :return: DriveEntity with permissions
    :rtype: frappe._dict
    """

    fields = fields or [
        "name",
        "title",
        "is_group",
        "owner",
        "modified",
        "file_size",
        "mime_type",
    ]
    my_entities = frappe.db.get_list(
        "Drive Entity",
        filters={
            "is_active": 1,
            "owner": frappe.session.user,
            "name": ["!=", get_user_directory().name],
        },
        fields=fields,
    )

    shared_entities = get_shared_with_me(get_all=True)

    all_entities = shared_entities + my_entities
    return list({x["name"]: x for x in all_entities}.values())


def get_valid_breadcrumbs(entity, user_access):
    """
    Determine user access and generate upward path (breadcrumbs).
    """
    file_path = generate_upward_path(entity.name)
    if user_access.get("type") in ["admin", "team"]:
        return file_path
    permission_path = get_shared_breadcrumbs(entity.nam, user_access.type)
    x = file_path[: -len(permission_path)]
    for i in reversed(x):
        if i.owner == frappe.session.user:
            permission_path.insert(0, i)
    file_path = permission_path
    return file_path


@frappe.whitelist()
def get_general_access(entity_name):
    """
    Return the general access permissions for the given entity

    :param entity_name: Document-name of the entity whose permissions are to be fetched
    :return: Dict of general access permissions (read, write)
    :rtype: frappe._dict or None
    """
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    fields = [
        DriveDocShare.name,
        DriveDocShare.read,
        DriveDocShare.write,
        DriveDocShare.share,
        DriveDocShare.everyone,
        DriveDocShare.public,
    ]
    query = (
        frappe.qb.from_(DriveDocShare)
        .select(*fields)
        .where(
            (DriveDocShare.share_name == entity_name)
            & ((DriveDocShare.everyone == True) | (DriveDocShare.public == True))
        )
        .groupby(DriveDocShare.name)
    )
    return query.run(as_dict=True)


def get_user_access(entity, user=None):
    """
    Return the user specific access permissions for an entity if it exists or general access permissions

    :param entity_name: Document-name of the entity whose permissions are to be fetched
    :return: Dict of general access permissions (read, write)
    :rtype: frappe._dict or None
    """
    fields = ["read", "comment", "write", "share", "name as permission_name", "valid_until"]
    NO_ACCESS = {
        "read": 0,
        "comment": 0,
        "share": 0,
        "write": 0,
    }
    if not user:
        user = frappe.session.user

    # If unauthorized
    if frappe.session.user == "Guest":
        public_access = frappe.db.get_value(
            "Drive Permission",
            {"entity": entity.name, "user": None},
            fields,
            as_dict=1,
        )
        if public_access:
            return public_access
        return NO_ACCESS

    # If logged in, first get Permission
    user_access = frappe.db.get_value(
        "Drive Permission",
        {
            "entity": entity.name,
            "user": user,
        },
        fields,
        as_dict=1,
    )
    if user_access:
        return user_access

    # Otherwise, check team/admin/owner
    teams = get_teams(user)
    if user == entity.owner:
        return {"read": 1, "comment": 1, "share": 1, "write": 1, "type": "admin"}
    if entity.team in teams:
        # Allow write access for uploading to home folder
        if entity.parent_entity == None:
            return {"read": 1, "comment": 1, "share": 0, "write": 1, "type": "team"}
        return {"read": 1, "comment": 1, "share": 1, "write": 0, "type": "team"}

    return NO_ACCESS


def user_group_entity_access(entity_name=None, user=None):
    """
    Get user group access level for current user and current entity

    :param entity_name: Document-name of the folder whose contents are to be listed. Defaults to the user directory
    :param order_by: Sort the list of results according to the specified field (eg: 'modified desc'). Defaults to 'title'
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :raises PermissionError: If the user does not have access to the specified folder
    :return: List of DriveEntity records
    :rtype: list
    """
    if not user:
        user = frappe.session.user
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    UserGroup = frappe.qb.DocType("User Group")
    UserGroupMember = frappe.qb.DocType("User Group Member")
    selectedFields = [
        DriveDocShare.user_name,
        DriveDocShare.read,
        DriveDocShare.write,
        DriveDocShare.share,
        DriveDocShare.name.as_("docshare_name"),
    ]

    query = (
        frappe.qb.from_(DriveDocShare)
        .join(UserGroupMember)
        .on((UserGroupMember.parent == DriveDocShare.user_name))
        .select(*selectedFields)
        .where((DriveDocShare.share_name == entity_name) & (UserGroupMember.user == user))
        .groupby(UserGroupMember.name)
    )
    result = query.run(as_dict=True)
    if not result:
        return False
    return max(result, key=lambda x: x["write"])


def has_app_permission():
    user = frappe.session.user

    if user == "Administrator":
        return True

    roles_to_check = {"Drive Admin", "Drive User", "Drive Guest", "System Manager"}
    user_roles = frappe.get_roles(user)

    return not roles_to_check.isdisjoint(user_roles)


@frappe.whitelist()
def update_document_invalidation(entity_name, invalidation_date):
    x = frappe.get_list(
        "Drive DocShare",
        filters={"share_name": entity_name, "share_doctype": "Drive Entity"},
        order_by="creation desc",
        fields=["name", "valid_until", "share_parent"],
    )
    for i in x:
        doc = frappe.get_doc("Drive DocShare", i.name)
        doc.valid_until = invalidation_date
        doc.save()


@frappe.whitelist()
def update_document_invalidation(entity_name, invalidation_date):
    x = frappe.get_list(
        "Drive DocShare",
        filters={"share_name": entity_name, "share_doctype": "Drive Entity"},
        order_by="creation desc",
        fields=["name", "valid_until", "share_parent"],
    )
    for i in x:
        doc = frappe.get_doc("Drive DocShare", i.name)
        doc.valid_until = invalidation_date
        doc.save()


def batch_delete_docshares(docshares):
    for document in docshares:
        frappe.delete_doc("Drive DocShare", document.name)


def auto_delete_expired_docshares():
    current_date = getdate()
    expired_documents = frappe.get_list(
        "Drive DocShare",
        filters=[
            ["valid_until", "<", current_date],
            ["valid_until", "is", "set"],
            ["protected", "!=", 1],
        ],
        order_by="creation desc",
        fields=["name", "valid_until"],
    )
    if expired_documents:
        frappe.enqueue(batch_delete_docshares, docshares=expired_documents)
    return


def get_shared_breadcrumbs(name, type=None):
    """
    given a node return the root. stops when share_parent IS NULL
    given a node and parent travel till
    the child of the parent_entity and append the parent_entity
    """
    share_name = frappe.db.escape(share_name)
    result = frappe.db.sql(
        f"""
        WITH RECURSIVE generated_path as ( 
        SELECT 
            `tabDrive DocShare`.name,
            `tabDrive DocShare`.share_name,
            `tabDrive DocShare`.share_parent
        FROM `tabDrive DocShare` 
        WHERE `tabDrive DocShare`.name = {share_name}

        UNION ALL

        SELECT 
            `tabDrive DocShare`.name,
            `tabDrive DocShare`.share_name,
            `tabDrive DocShare`.share_parent
        FROM generated_path as gp
        JOIN `tabDrive DocShare` ON `tabDrive DocShare`.name = gp.share_parent
        ) 
        SELECT * FROM generated_path;
    """,
        as_dict=1,
    )
    share_breadcrumbs = []
    for i in result:
        share_breadcrumbs.append(
            frappe.get_value(
                "Drive Entity",
                i.share_name,
                ["name", "title", "parent_drive_entity", "owner"],
                as_dict=1,
            )
        )
    return share_breadcrumbs[::-1]
