import frappe
import json
from drive.utils.files import get_user_directory
from pypika import Order, Criterion, Case, functions as fn

DriveUser = frappe.qb.DocType("User")
UserGroupMember = frappe.qb.DocType("User Group Member")
DriveEntity = frappe.qb.DocType("Drive Entity")
DriveFavourite = frappe.qb.DocType("Drive Favourite")
DriveDocShare = frappe.qb.DocType("Drive DocShare")
DriveRecent = frappe.qb.DocType("Drive Entity Log")

parent_folder = None
query = None


def validate_parent(entity_name):
    entity_name, is_group, is_active = frappe.db.get_value(
        "Drive Entity", entity_name, ["name", "is_group", "is_active"]
    )
    if not is_group:
        frappe.throw("Specified entity is not a folder", NotADirectoryError)
    if not is_active:
        frappe.throw("Specified folder has been trashed by the owner")
    return


def eval_general_access(entity_name):
    is_public = False
    if frappe.db.exists(
        {
            "doctype": "Drive DocShare",
            "share_doctype": "Drive Entity",
            "share_name": entity_name,
            "public": 1,
        }
    ):
        is_public = True
    return "public" if is_public else "everyone"


@frappe.whitelist(allow_guest=True)
def files(
    entity_name=None,
    order_by="modified",
    is_active=1,
    limit=100,
    offset=0,
    folders_first=True,
    favourites_only=False,
    recents_only=False,
    file_kind_list=[],
    mime_type_list=[],
):
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
        DriveDocShare.user_name,
        DriveDocShare.user_doctype,
        DriveDocShare.write,
        DriveDocShare.public,
        DriveDocShare.everyone,
        DriveDocShare.share,
        DriveFavourite.entity.as_("is_favourite"),
    ]
    favourites_only = json.loads(favourites_only)
    recents_only = json.loads(recents_only)
    general_access = eval_general_access(entity_name)
    
    if mime_type_list and not entity_name:
        entity_name = get_user_directory(frappe.session.user).name

    if recents_only:
        selectedFields.append(DriveRecent.last_interaction.as_("modified"))
    query = (
        frappe.qb.from_(DriveEntity)
        .left_join(DriveDocShare)
        .on((DriveDocShare.share_name == DriveEntity.name))
        .left_join(UserGroupMember)
        .on((UserGroupMember.parent == DriveDocShare.user_name))
        .left_join(DriveUser)
        .on((DriveEntity.owner == DriveUser.email))
        .offset(offset)
        .limit(limit)
        .select(*selectedFields)
    )
    if entity_name:
        query = query.where(DriveEntity.parent_drive_entity == entity_name)
    query = query.where(
        (DriveEntity.is_active == is_active)
        & (
            (UserGroupMember.user == frappe.session.user)
            | (
                (DriveDocShare.user_name == frappe.session.user)
                | (DriveDocShare[general_access] == 1)
                | (DriveEntity.owner == frappe.session.user)
            )
        )
    )
    if folders_first:
        query = query.orderby(
            Case().when(DriveEntity.is_group == True, 1).else_(2),
            Order.desc,
        )
    if favourites_only:
        query = query.right_join(DriveFavourite).on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
    else:
        query = query.left_join(DriveFavourite).on(
            (DriveFavourite.entity == DriveEntity.name)
            & (DriveFavourite.user == frappe.session.user)
        )
    if recents_only:
        query = (
            query.right_join(DriveRecent)
            .on(
                (DriveRecent.entity_name == DriveEntity.name)
                & (DriveRecent.user == frappe.session.user)
            )
            .orderby(DriveRecent.last_interaction, order=Order.desc)
        )
    else:
        query = query.orderby(
            order_by.split()[0],
            order=Order.desc if order_by.endswith("desc") else Order.asc,
        )

    if file_kind_list:
        file_kind_list = json.loads(file_kind_list)
        file_kind_criterion = [DriveEntity.file_kind == file_kind for file_kind in file_kind_list]
        query = query.where(Criterion.any(file_kind_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        mime_type_criterion = [DriveEntity.mime_type == mime_type for mime_type in mime_type_list]
        query = query.where((Criterion.any(mime_type_criterion)) | (DriveEntity.is_group == True))

    query = query.groupby(DriveEntity.name)
    result = query.run(as_dict=True)
    return result


@frappe.whitelist()
def shared_with_user(
    order_by="modified",
    limit=100,
    offset=0,
    folders_first=True,
    file_kind_list=[],
    mime_type_list=[],
):
    """
    Returns the highest level of shared items shared with/by the current user, group or org

    :param entity_name: Document-name of the folder whose contents are to be listed.
    :raises NotADirectoryError: If this DriveEntity doc is not a folder
    :return: List of DriveEntities with permissions
    :rtype: list[frappe._dict]
    """

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
    mime_type_list=[],
):
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

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        mime_type_criterion = [DriveEntity.mime_type == mime_type for mime_type in mime_type_list]
        query = query.where((Criterion.any(mime_type_criterion)) | (DriveEntity.is_group == True))

    return query.run(as_dict=True)
