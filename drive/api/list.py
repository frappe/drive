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
    limit=100,
    favourites_only=0,
    recents_only=0,
    tag_list=[],
    mime_type_list=[],
    personal=0,
    folders=0,
    all=0,
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
        .where(Entity.is_active == is_active)
        .left_join(DrivePermission)
        .on(
            (DrivePermission.entity == Entity.name) & (DrivePermission.user == frappe.session.user)
        )
        .limit(limit)
        # Give defaults as a team member
        .select(
            *ENTITY_FIELDS,
            fn.Coalesce(DrivePermission.read, 1).as_("read"),
            fn.Coalesce(DrivePermission.comment, 1).as_("comment"),
            fn.Coalesce(DrivePermission.share, 1).as_("share"),
            fn.Coalesce(DrivePermission.write, DriveEntity.owner == frappe.session.user).as_(
                "write"
            ),
        )
        .where(fn.Coalesce(DrivePermission.read, 1).as_("read") == 1)
    )

    if all:
        query = query.where(Entity.team == team)
    else:
        query = query.where(Entity.parent_entity == entity_name)

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
    if personal:
        query = query.where(
            (Entity.is_private == personal) & (Entity.owner == frappe.session.user)
        )
    elif favourites_only or recents_only or not is_active:
        query = query.where((Entity.is_private == 0) | (Entity.owner == frappe.session.user))
    else:
        query = query.where(Entity.is_private == 0)

    query = query.select(Recents.last_interaction.as_("accessed"))

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        query = query.where(
            Criterion.any(Entity.mime_type == mime_type for mime_type in mime_type_list)
        )
    if folders:
        query = query.where(Entity.is_group == 1)
    return query.run(as_dict=True)


@frappe.whitelist()
def shared(
    by=0,
    order_by="modified",
    limit=100,
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
    by = int(by)
    query = (
        frappe.qb.from_(Entity)
        .right_join(DrivePermission)
        .on(
            (DrivePermission.entity == Entity.name)
            & ((DrivePermission.owner if by else DrivePermission.user) == frappe.session.user)
        )
        .limit(limit)
        .where((DrivePermission.read == 1) & (Entity.is_active == 1))
        .select(*ENTITY_FIELDS, DrivePermission.user, DrivePermission.owner.as_("sharer"))
    )

    query = query.orderby(
        order_by.split()[0],
        order=Order.desc if order_by.endswith("desc") else Order.asc,
    )

    if tag_list:
        tag_list = json.loads(tag_list)
        query = query.left_join(DriveEntityTag).on(DriveEntityTag.parent == DriveEntity.name)
        tag_list_criterion = [DriveEntityTag.tag == tags for tags in tag_list]
        query = query.where(Criterion.any(tag_list_criterion))

    if mime_type_list:
        mime_type_list = json.loads(mime_type_list)
        query = query.where(
            Criterion.any(Entity.mime_type == mime_type for mime_type in mime_type_list)
        )
    return query.run(as_dict=True)
