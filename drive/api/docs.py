from datetime import datetime

import frappe
from frappe.rate_limiter import rate_limit

from drive.utils import strip_comment_spans

from .permissions import user_has_permission


@frappe.whitelist(allow_guest=True)
def save_doc_comment(entity_name, doc_name, content):
    if not user_has_permission(entity_name, "comment"):
        raise frappe.PermissionError("You do not have permission to comment on this file")


@frappe.whitelist(allow_guest=True)
@rate_limit(key="create_comment", limit=10, seconds=1)
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
    if comment.owner != frappe.session.user and comment.user != "Guest":
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


@frappe.whitelist(allow_guest=True)
def get_wiki_link(title, team):
    title = title.strip("/")
    possible_titles = [title, title + ".md", title + ".txt"]
    names = (
        frappe.get_value("Drive File", {"title": k, "team": team, "is_group": 0}, "name")
        for k in possible_titles
    )
    try:
        name = next(k for k in names if k)
    except StopIteration:
        frappe.throw("Cannot get this wikilink in this team.", frappe.NotFound)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/drive/f/" + name
    return title


@frappe.whitelist()
def create_version(doc, snapshot, manual=0, title="", duration=""):
    doc = frappe.get_doc("Drive Document", doc)
    title = title if title else str(datetime.now())[:16]

    if not manual and duration:
        last_version = frappe.db.get_value({"doctype": "Drive Doc Version", "parent": doc.name, "title": title}):

    doc.append(
        "versions",
        {
            "snapshot": snapshot,
            "manual": int(manual),
            "title": title,
        },
    )
    doc.save()
    return doc
