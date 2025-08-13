import frappe


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
    existing = frappe.db.get_value(
        "Comment",
        {
            "comment_type": "Like",
            "reference_doctype": "Comment",
            "reference_name": comment_id,
            "comment_email": user,
            "content": emoji,
        },
        "name",
    )

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
                comment_content=parent.content,
            )
    except Exception:
        # Do not block on notification errors
        pass

    return {"status": "added"}


