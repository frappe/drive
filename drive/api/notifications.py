import frappe
import json
from pypika import Order


@frappe.whitelist()
def get_notifications(only_unread):
    """
    Get notifications for current user

    :param only_unread: only get notifications where read is False 
    """
    User = frappe.qb.DocType("User")
    Notification = frappe.qb.DocType("Drive Notification")
    fields = [
        Notification.name,
        Notification.to_user,
        Notification.from_user,
        Notification.read,
        Notification.type,
        Notification.message,
        Notification.entity_type,
        Notification.notif_doctype,
        Notification.notif_doctype_name,
        Notification.creation,
        User.user_image,
        User.full_name,
    ]
    query = (
        frappe.qb.from_(Notification)
        .inner_join(User)
        .on(Notification.from_user == User.name)
        .select(*fields)
        .orderby(Notification.creation, order=Order.desc)
    )

    if only_unread:
        query = query.where(Notification.read == 0)
    query = query.where(Notification.to_user == frappe.session.user)
    result = query.run(as_dict=True)
    return result


@frappe.whitelist()
def get_unread_count():
    """
    Return a count of records where user is current user and read is False
    """
    return frappe.db.count(
        "Drive Notification", filters={"to_user": frappe.session.user, "read": 0}
    )


@frappe.whitelist()
def mark_as_read(name=None, all=False):
    """
    Mark notification for current user as read 

    :param name: ID of notification record 
    :param all: Will mark all unread notifications as read
    """
    if all:
        frappe.db.set_value(
            "Drive Notification", {"to_user": frappe.session.user, "read": False}, "read", True
        )
        return
    frappe.db.set_value("Drive Notification", name, "read", True)
    return


def notify_mentions(entity_name, document_name):
    """
    Create a mention notification for each user mentioned 
    :param entity_name: ID of entity
    :param document_name: ID of document containing mentions
    """
    entity = frappe.get_doc("Drive Entity", entity_name)
    document = frappe.get_doc("Drive Document", document_name)
    if not document.mentions:
        return
    mentions = json.loads(document.mentions)
    for mention in mentions:
        if mention["type"] == "User":
            author_full_name = frappe.db.get_value(
                "User", {"name": mention["author"]}, ["full_name"]
            )
            message = f' {author_full_name} mentioned you in document "{entity.title}"'
            create_notification(mention["author"], mention["id"], "Mention", entity, message)
        if mention["type"] == "User Group":
            group_users = frappe.get_all(
                "User Group Member", filters={"parent": mention["id"]}, fields="user"
            )
            message = (
                f' {author_full_name} mentioned {mention["id"]} group in document "{entity.title}"'
            )
            for user in group_users:
                if user.user == frappe.session.user:
                    continue
                create_notification(mention["author"], user.user, "Mention", entity, message)


def notify_share(entity_name, docshare_name):
    """
    Create a share notification for each user 
    :param entity_name: ID of entity
    :param document_name: ID of docshare containing share info
    """
    entity = frappe.get_doc("Drive Entity", entity_name)
    docshare = frappe.get_doc("Drive DocShare", docshare_name)

    author_full_name = frappe.db.get_value("User", {"name": docshare.owner}, ["full_name"])
    entity_type = "document" if entity.document else "folder" if entity.is_group else "file"

    message = f'{author_full_name} shared {entity_type} "{entity.title}" with you'

    if docshare.user_doctype == "User":
        create_notification(docshare.owner, docshare.user_name, "Share", entity, message)

    if docshare.user_doctype == "User Group":
        group_users = frappe.get_all(
            "User Group Member", filters={"parent": docshare.user_name}, fields="user"
        )
        for user in group_users:
            if user.user == frappe.session.user:
                continue
            create_notification(docshare.owner, user.user, "Share", entity, message)

    if docshare.everyone:
        drive_users = frappe.get_all(
            doctype="User",
            order_by="full_name",
            filters=[
                ["Has Role", "role", "=", "Drive User"],
                ["full_name", "not like", "Administrator"],
                ["full_name", "not like", "Guest"],
            ],
            fields=[
                "email",
            ],
        )
        for user in drive_users:
            if user.email == frappe.session.user:
                continue
            create_notification(docshare.owner, user.email, "Share", entity, message)
        return


def create_notification(from_user, to_user, type, entity, message=None):
    """
    Create a notification
    :param from_user: notification owner user email
    :param to_user: notification receiver user email 
    :param type: subject of notification
    :param entity: drive_entity name 
    :param message: notification message
    """
    from drive.api.permissions import get_user_access

    user_access = get_user_access(entity.name, to_user)
    if user_access.get("read") == 0:
        return
    entity_type = "Document" if entity.document else "Folder" if entity.is_group else "File"
    notif = frappe.get_doc(
        {
            "doctype": "Drive Notification",
            "from_user": from_user,
            "to_user": to_user,
            "type": type,
            "entity_type": entity_type,
            "notif_doctype": "Drive Entity",
            "notif_doctype_name": entity.name,
            "message": message,
        }
    )
    try:
        notif.insert()
    except frappe.exceptions.ValidationError as e:
        print(f"Error inserting document: {e}")
