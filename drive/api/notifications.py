import frappe
import json
from pypika import Order


def get_link(entity):
    type_ = {True: "file", bool(entity.is_group): "folder", bool(entity.document): "document"}
    return (
        entity.path
        if entity.is_link
        else f"/drive/t/{entity.team}/{type_.get(True)}/{entity.name}/"
    )


def get_team_members(team_name):
    """
    Get all members of a team
    :param team_name: Name of the team
    :return: List of team member users
    """
    team = frappe.get_doc("Drive Team", team_name)
    team_members = []
    if team.users:
        for member in team.users:
            team_members.append(member.user)
    return team_members


def notify_team_file_upload(doc, method=None):
    """
    Notify all team members when a new file/folder is uploaded/created
    :param doc: Drive File document object
    :param method: Method name (from hook)
    """
    try:
        # Skip if entity is private
        if doc.is_private:
            return

        # Get team members
        team_members = get_team_members(doc.team)

        # Get current user info
        current_user = frappe.session.user
        current_user_full_name = frappe.db.get_value("User", current_user, "full_name")

        # Determine entity type and action
        if doc.is_group:
            entity_type = "folder"
            action = "tạo"
        elif doc.document:
            entity_type = "document"
            action = "tạo"
        else:
            entity_type = "file"
            action = "tải"

        message = f'{current_user_full_name} đã {action} một {entity_type} mới: "{doc.title}"'

        # Send notification to all team members except the current user
        for member in team_members:
            if member != current_user:
                create_notification(
                    from_user=current_user,
                    to_user=member,
                    type="File Upload",
                    entity=doc,
                    message=message,
                )

    except Exception as e:
        print(f"Error sending team notifications: {e}")


def notify_team_folder_creation(entity_name):
    """
    Notify all team members when a new folder is created
    :param entity_name: Name of the Drive File entity
    """
    try:
        entity = frappe.get_doc("Drive File", entity_name)

        # Skip if entity is private
        if entity.is_private:
            return

        # Get team members
        team_members = get_team_members(entity.team)

        # Get current user info
        current_user = frappe.session.user
        current_user_full_name = frappe.db.get_value("User", current_user, "full_name")

        message = f'{current_user_full_name} đã tạo một folder mới: "{entity.title}"'

        # Send notification to all team members except the current user
        for member in team_members:
            if member != current_user:
                create_notification(
                    from_user=current_user,
                    to_user=member,
                    type="Folder Creation",
                    entity=entity,
                    message=message,
                )

    except Exception as e:
        print(f"Error sending team folder notifications: {e}")


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
        .left_join(User)
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
    entity = frappe.get_doc("Drive File", entity_name)
    document = frappe.get_doc("Drive Document", document_name)
    if not document.mentions:
        return
    mentions = json.loads(document.mentions)
    for mention in mentions:
        author_full_name = frappe.db.get_value("User", {"name": mention["author"]}, ["full_name"])
        message = f' {author_full_name} mentioned you in document "{entity.title}"'
        create_notification(mention["author"], mention["id"], "Mention", entity, message)


def notify_share(entity_name, docperm_name):
    """
    Create a share notification for each user
    :param entity_name: ID of entity
    :param document_name: ID of docshare containing share info
    """
    entity = frappe.get_doc("Drive File", entity_name)
    docshare = frappe.get_doc("Drive Permission", docperm_name)

    author_full_name = frappe.db.get_value("User", {"name": docshare.owner}, ["full_name"])
    entity_type = "document" if entity.document else "folder" if entity.is_group else "file"

    message = f'{author_full_name} đã chia sẻ một {entity_type} với bạn: "{entity.title}"'
    create_notification(docshare.owner, docshare.user, "Share", entity, message)
    send_share_email(docshare.user, message, get_link(entity), entity.team, entity_type)


def create_notification(from_user, to_user, type, entity, message=None, comment_id: str = None):
    """
    Create a notification
    :param from_user: notification owner user email
    :param to_user: notification receiver user email
    :param type: subject of notification
    :param entity: drive_file name
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
            "notif_doctype": "Drive File",
            "notif_doctype_name": entity.name,
            "message": message,
            "id_team": entity.team,
            "file_name": entity.title,
            "comment_id": comment_id,
        }
    )
    try:
        notif.insert()
        print("========================= insert: ", flush=True)
        print(f"Notification created: {notif.type}")
    except frappe.exceptions.ValidationError as e:
        print(f"Error inserting document: {e}")


def notify_comment_mentions(entity_name, comment_doc, mentions):
    """
    Create a mention notification for each user mentioned in a comment
    :param entity_name: ID of entity
    :param comment_doc: Comment document instance
    :param mentions: List of mentions from frontend
    """
    entity = frappe.get_doc("Drive File", entity_name)
    for mention in mentions:
        author_full_name = frappe.db.get_value(
            "User", {"name": comment_doc.comment_email}, ["full_name"]
        )
        message = f'{author_full_name} mentioned you in a comment on "{entity.title}"'
        create_notification(
            comment_doc.comment_email,
            mention["id"],
            "Mention",
            entity,
            message,
            comment_id=comment_doc.name,
        )


def send_share_email(to, message, link, team, type_):
    frappe.sendmail(
        recipients=to,
        subject=f"Frappe Drive - {type_.capitalize()} Shared",
        template="drive_share",
        args={
            "message": message,
            "type": type_,
            "link": link,
            "team_name": frappe.db.get_value("Drive Team", team, "title"),
        },
        now=True,
    )
