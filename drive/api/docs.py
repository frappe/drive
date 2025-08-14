import frappe

from .permissions import user_has_permission


@frappe.whitelist()
def create_comment(entity_name, name, content, is_reply, parent_name=None):
    doc = frappe.get_doc("Drive File", entity_name)
    parent = frappe.get_doc("Drive Comment", parent_name) if is_reply else doc

    if not user_has_permission(doc, "comment"):
        raise PermissionError("You don't have comment access")

    comment = frappe.get_doc(
        {
            "doctype": "Drive Comment",
            "name": name,
            "content": content,
        }
    )
    parent.append("replies" if is_reply else "comments", comment)
    parent.save(ignore_permissions=True)
    comment.insert(ignore_permissions=True)
    return comment.name


@frappe.whitelist()
def edit_comment(name, content):
    comment = frappe.get_doc("Drive Comment", name)
    if comment.owner != frappe.session.user:
        raise PermissionError("You can't edit comments you don't own.")
    comment.content = content
    comment.save()
    return name


@frappe.whitelist()
def delete_comment(name, entire=True):
    comment = frappe.get_doc("Drive Comment", name)
    if comment.owner != frappe.session.user:
        raise PermissionError("You can't edit comments you don't own.")
    if entire:
        for r in comment.replies:
            r.delete()
    comment.delete()


@frappe.whitelist()
def resolve_comment(name, value):
    comment = frappe.get_doc("Drive Comment", name)
    comment.resolved = value
    comment.save()
