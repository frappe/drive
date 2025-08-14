import frappe
import unicodedata
import json
from raven.raven_bot.doctype.raven_bot.raven_bot import RavenBot


@frappe.whitelist()
def react_to_comment(comment_id: str, emoji: str):
    """Toggle a reaction (emoji) on a Comment by the current user.

    Reactions are stored as rows in the standard Comment doctype with:
    - comment_type = "Like"
    - reference_doctype = "Comment"
    - reference_name = parent comment id
    - content = emoji character
    - comment_email = current user

    If a matching reaction already exists for the user, it will be removed
    (toggle off). Otherwise, it is created and a notification is sent to the
    owner of the original comment.
    """

    # Validate parent comment
    parent = frappe.get_value(
        "Comment",
        {"name": comment_id, "comment_type": "Comment", "reference_doctype": "Drive File"},
        ["name", "reference_name", "comment_email", "content"],
        as_dict=True,
    )
    if not parent:
        frappe.throw("Comment not found", frappe.DoesNotExistError)

    user = frappe.session.user
    # Find existing reaction by the same user and emoji

    normalized_emoji = unicodedata.normalize("NFC", emoji.strip())
    # Fetch all reactions for this comment by this user
    reactions = frappe.get_all(
        "Comment",
        filters={
            "comment_type": "Like",
            "reference_doctype": "Comment",
            "reference_name": comment_id,
            "comment_email": user,
        },
        fields=["name", "content"],
    )
    existing = None
    for reaction in reactions:
        if unicodedata.normalize("NFC", (reaction["content"] or "").strip()) == normalized_emoji:
            existing = reaction["name"]
            break

    if existing:
        # Toggle off -> delete existing reaction
        frappe.delete_doc("Comment", existing)
        return {"status": "removed"}

    # Otherwise, create a new reaction comment
    reaction = frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Like",
            "reference_doctype": "Comment",
            "reference_name": comment_id,
            "comment_email": user,
            "comment_by": frappe.db.get_value("User", user, "full_name"),
            "content": emoji,
        }
    )
    reaction.insert(ignore_permissions=True)

    # Notify the owner of the original comment (if different user)
    try:
        if parent.comment_email and parent.comment_email != user:
            from drive.api.notifications import create_notification

            entity = frappe.get_doc("Drive File", parent.reference_name)
            reactor_full_name = frappe.db.get_value("User", user, "full_name")
            message = f'{reactor_full_name} reacted "{emoji}" to your comment on "{entity.title}"'
            create_notification(
                from_user=user,
                to_user=parent.comment_email,
                type="Reaction",
                entity=entity,
                message=message,
                comment_id=parent.name,
            )

            # Send bot notification
            bot_docs = frappe.conf.get("bot_docs")
            if not bot_docs:
                return

            message_data = {
                "key": "reaction_comment_document",
                "title": f'{reactor_full_name} đã thả {emoji} vào bình luận của bạn trong "{entity.title}": "{parent.content}" + {emoji}',
                "full_name_owner": reactor_full_name,
                "to_user": parent.comment_email,
                "message": message,
                "file_name": entity.title,
                "emoji": emoji,
                "comment_content": parent.content or "",
                "link": f"/drive/t/{entity.team}/file/{entity.name}",
            }

            RavenBot.send_notification_to_user(
                bot_name=bot_docs,
                user_id=parent.comment_email,
                message=json.dumps(message_data, ensure_ascii=False, default=str),
            )
    except Exception:
        # Do not block on notification errors
        pass

    return {"status": "added"}
