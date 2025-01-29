import frappe
import json
from drive.utils.files import get_home_folder
from .permissions import get_teams, ENTITY_FIELDS
from pypika import Order, Criterion, Case, functions as fn

DriveUser = frappe.qb.DocType("User")
UserGroupMember = frappe.qb.DocType("User Group Member")
DriveEntity = frappe.qb.DocType("Drive Entity")
DrivePermission = frappe.qb.DocType("Drive Permission")
Entity = frappe.qb.DocType("Drive Entity")
Team = frappe.qb.DocType("Drive Team")
TeamMember = frappe.qb.DocType("Drive Team Member")
DriveFavourite = frappe.qb.DocType("Drive Favourite")
DriveDocShare = frappe.qb.DocType("Drive DocShare")
Recents = frappe.qb.DocType("Drive Entity Log")
DriveEntityTag = frappe.qb.DocType("Drive Entity Tag")


@frappe.whitelist()
def files(
    team,
    entity_name=None,
    order_by="title",
    is_active=1,
    offset=0,
    favourites_only=0,
    recents_only=0,
    tag_list=[],
    mime_type_list=[],
):
    teams = get_teams()
    if team not in teams:
        frappe.throw("Team doesn't exist", frappe.exceptions.PageDoesNotExistError)

    if not entity_name:
        # If not specified, get home folder
        entity_name = get_home_folder(team)["name"]
    else:
        # Verify that entity exists and is part of the team
        if not frappe.qb.from_(Entity).where((Entity.name == entity_name) & (Entity.team == team)):
            frappe.throw("Not found", frappe.exceptions.PageDoesNotExistError)

    # Get all the children entities
    query = (
        frappe.qb.from_(Entity)
        .where(Entity.parent_entity == entity_name)
        .where(Entity.is_active == is_active)
        .left_join(DrivePermission)
        .on(
            (DrivePermission.entity == Entity.name) & (DrivePermission.user == frappe.session.user)
        )
        .offset(offset)
        .limit(100)
        # Give defaults as a team member
        .select(
            *ENTITY_FIELDS,
            fn.Coalesce(DrivePermission.read, 1).as_("read"),
            fn.Coalesce(DrivePermission.comment, 1).as_("comment"),
            fn.Coalesce(DrivePermission.share, 1).as_("share"),
            fn.Coalesce(DrivePermission.write, 0).as_("write"),
        )
    )

    # Get favourites data (only that, if applicable)
    if favourites_only:
        query = query.right_join(DriveFavourite)
    else:
        query = query.left_join(DriveFavourite)
    query = query.on(
        (DriveFavourite.entity == Entity.name) & (DriveFavourite.user == frappe.session.user)
    ).select(DriveFavourite.name.as_("is_favourite"))

    if recents_only:
        query = (
            query.right_join(Recents)
            .on((Recents.entity_name == Entity.name) & (Recents.user == frappe.session.user))
            .orderby(Recents.last_interaction, order=Order.desc)
        )
    else:
        query = (
            query.left_join(Recents).on(
                (Recents.entity_name == Entity.name) & (Recents.user == frappe.session.user)
            )
        ).orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )

    query = query.select(Recents.last_interaction.as_("accessed"))

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        query = query.where(
            Criterion.any(DriveEntity.mime_type == mime_type for mime_type in mime_type_list)
        )

    return query.run(as_dict=True)


@frappe.whitelist()
def shared_with_user(
    order_by="modified",
    limit=100,
    offset=0,
    folders_first=True,
    file_kind_list=[],
    tag_list=[],
    mime_type_list=[],
):
    """
    Returns the highest level of shared items shared with/by the current user, group or org

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """
    if isinstance(folders_first, str):
        try:
            folders_first = json.loads(folders_first)
        except json.JSONDecodeError:
            frappe.log_error(
                "Invalid JSON for folders_first: {}".format(folders_first), "JSONDecodeError"
            )
            folders_first = True
    folders_first = bool(folders_first)
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
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
        DriveEntity.file_kind,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_download,
        DriveEntity.is_active,
        DriveEntity.allow_comments,
        DriveDocShare.user_name,
        DriveDocShare.user_doctype,
        DriveDocShare.read,
        DriveDocShare.write,
        DriveDocShare.everyone,
        DriveDocShare.share,
        DriveDocShare.share_parent,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .inner_join(DriveDocShare)
        .on((DriveDocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on((UserGroupMember.parent == DriveDocShare.user_name))
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
        .where(DriveEntity.is_active == 1)
        .where(
            (UserGroupMember.user == frappe.session.user)
            | (DriveDocShare.user_name == frappe.session.user)
            | (DriveDocShare.everyone == 1)
            | (DriveDocShare.public == 1)
        )
        .where(DriveDocShare.share_parent.isnull())
        .where(DriveEntity.owner != frappe.session.user)
        .groupby(DriveEntity.name)
    )
    if folders_first:
        query = query.orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )

    query = query.orderby(
        order_by.split()[0],
        order=Order.desc if order_by.endswith("desc") else Order.asc,
    )
    if file_kind_list:
        file_kind_list = json.loads(file_kind_list)
        file_kind_criterion = [DriveEntity.file_kind == file_kind for file_kind in file_kind_list]
        query = query.where(Criterion.any(file_kind_criterion))

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        mime_type_criterion = [DriveEntity.mime_type == mime_type for mime_type in mime_type_list]
        query = query.where((Criterion.any(mime_type_criterion)) | (DriveEntity.is_group == True))

    return query.run(as_dict=True)


@frappe.whitelist()
def shared_by_user(
    order_by="modified",
    limit=100,
    offset=0,
    folders_first=True,
    file_kind_list=[],
    tag_list=[],
    mime_type_list=[],
):
    """
    Return the list of files and folders shared with the current user

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """
    if isinstance(folders_first, str):
        try:
            folders_first = json.loads(folders_first)
        except json.JSONDecodeError:
            frappe.log_error(
                "Invalid JSON for folders_first: {}".format(folders_first), "JSONDecodeError"
            )
            folders_first = True
    folders_first = bool(folders_first)
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
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
        DriveEntity.file_kind,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_download,
        DriveEntity.is_active,
        DriveEntity.allow_comments,
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
        .where(DriveEntity.is_active == 1)
        .where(
            (DriveDocShare.user_name != frappe.session.user)
            | (DriveDocShare.everyone == 1)
            | (DriveDocShare.public == 1)
        )
        .where(DriveDocShare.owner_parent.isnull())
        .groupby(DriveEntity.name)
    )
    if folders_first:
        query = query.orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )

    query = query.orderby(
        order_by.split()[0],
        order=Order.desc if order_by.endswith("desc") else Order.asc,
    )
    if file_kind_list:
        file_kind_list = json.loads(file_kind_list)
        file_kind_criterion = [DriveEntity.file_kind == file_kind for file_kind in file_kind_list]
        query = query.where(Criterion.any(file_kind_criterion))

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        mime_type_criterion = [DriveEntity.mime_type == mime_type for mime_type in mime_type_list]
        query = query.where((Criterion.any(mime_type_criterion)) | (DriveEntity.is_group == True))

    return query.run(as_dict=True)


@frappe.whitelist()
def shared_with_guest(
    order_by="modified",
    limit=100,
    offset=0,
    folders_first=True,
    file_kind_list=[],
    tag_list=[],
    mime_type_list=[],
):
    """
    Returns the highest level of shared items shared with/by the current user, group or org

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """
    if isinstance(folders_first, str):
        try:
            folders_first = json.loads(folders_first)
        except json.JSONDecodeError:
            frappe.log_error(
                "Invalid JSON for folders_first: {}".format(folders_first), "JSONDecodeError"
            )
            folders_first = True
    folders_first = bool(folders_first)
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
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
        DriveEntity.file_kind,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_download,
        DriveEntity.is_active,
        DriveEntity.allow_comments,
        DriveDocShare.user_name,
        DriveDocShare.user_doctype,
        DriveDocShare.read,
        DriveDocShare.write,
        DriveDocShare.everyone,
        DriveDocShare.share,
        DriveDocShare.share_parent,
        DriveFavourite.entity.as_("is_favourite"),
    ]

    query = (
        frappe.qb.from_(DriveEntity)
        .inner_join(DriveDocShare)
        .on((DriveDocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on((UserGroupMember.parent == DriveDocShare.user_name))
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
        .where(DriveEntity.is_active == 1)
        .where(
            (UserGroupMember.user == frappe.session.user)
            | (DriveDocShare.user_name == frappe.session.user)
        )
        .where(DriveDocShare.share_parent.isnull())
        .where(DriveEntity.owner != frappe.session.user)
        .groupby(DriveEntity.name)
    )
    if folders_first:
        query = query.orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )

    query = query.orderby(
        order_by.split()[0],
        order=Order.desc if order_by.endswith("desc") else Order.asc,
    )
    if file_kind_list:
        file_kind_list = json.loads(file_kind_list)
        file_kind_criterion = [DriveEntity.file_kind == file_kind for file_kind in file_kind_list]
        query = query.where(Criterion.any(file_kind_criterion))

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        mime_type_criterion = [DriveEntity.mime_type == mime_type for mime_type in mime_type_list]
        query = query.where((Criterion.any(mime_type_criterion)) | (DriveEntity.is_group == True))

    return query.run(as_dict=True)


@frappe.whitelist()
def shared_by_guest(
    order_by="modified",
    limit=100,
    offset=0,
    folders_first=True,
    file_kind_list=[],
    tag_list=[],
    mime_type_list=[],
):
    """
    Return the list of files and folders shared with the current user

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """
    if isinstance(folders_first, str):
        try:
            folders_first = json.loads(folders_first)
        except json.JSONDecodeError:
            frappe.log_error(
                "Invalid JSON for folders_first: {}".format(folders_first), "JSONDecodeError"
            )
            folders_first = True
    folders_first = bool(folders_first)
    DriveDocShare = frappe.qb.DocType("Drive DocShare")
    DriveEntity = frappe.qb.DocType("Drive Entity")
    DriveFavourite = frappe.qb.DocType("Drive Favourite")
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
        DriveEntity.file_kind,
        DriveEntity.file_ext,
        DriveEntity.color,
        DriveEntity.document,
        DriveEntity.mime_type,
        DriveEntity.parent_drive_entity,
        DriveEntity.allow_download,
        DriveEntity.is_active,
        DriveEntity.allow_comments,
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
        .where(DriveEntity.is_active == 1)
        .where((DriveDocShare.user_name != frappe.session.user))
        .where(DriveDocShare.owner_parent.isnull())
        .groupby(DriveEntity.name)
    )
    if folders_first:
        query = query.orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )

    query = query.orderby(
        order_by.split()[0],
        order=Order.desc if order_by.endswith("desc") else Order.asc,
    )
    if file_kind_list:
        file_kind_list = json.loads(file_kind_list)
        file_kind_criterion = [DriveEntity.file_kind == file_kind for file_kind in file_kind_list]
        query = query.where(Criterion.any(file_kind_criterion))

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        mime_type_criterion = [DriveEntity.mime_type == mime_type for mime_type in mime_type_list]
        query = query.where((Criterion.any(mime_type_criterion)) | (DriveEntity.is_group == True))

    return query.run(as_dict=True)
