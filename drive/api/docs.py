from datetime import datetime, timedelta

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
        frappe.throw("You don't have comment access")

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
        frappe.throw("You can't edit comments you don't own.")
    comment.content = content
    comment.save()
    return name


@frappe.whitelist()
def delete_comment(name, entire=True):
    comment = frappe.get_doc("Drive Comment", name)
    if comment.owner != frappe.session.user and comment.user != "Guest":
        frappe.throw("You can't edit comments you don't own.")
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
    names = (frappe.get_value("Drive File", {"title": k, "team": team, "is_group": 0}, "name") for k in possible_titles)
    try:
        name = next(k for k in names if k)
    except StopIteration:
        frappe.throw("Cannot get this wikilink in this team.", frappe.NotFound)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = "/drive/f/" + name
    return title


@frappe.whitelist()
def create_version(doc, snapshot, duration=None, manual=0, title=""):
    if not manual:
        versions = frappe.get_all(
            "Drive Doc Version",
            filters={"parent": doc, "manual": 0},
            fields=["*"],
            order_by="idx desc",
            limit_page_length=1,
        )
        if versions:
            title = frappe.get_doc("Drive Doc Version", versions[0].name).title
            prev_time = datetime.strptime(title, "%Y-%m-%d %H:%M")
            now_time = datetime.now()
            diff = now_time - prev_time
            if diff < timedelta(minutes=duration):
                return False
            title = datetime.strftime(now_time, "%Y-%m-%d %H:%M")
        else:
            title = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M")

    doc = frappe.get_doc("Drive Document", doc)
    doc.append(
        "versions",
        {
            "snapshot": snapshot,
            "manual": int(manual),
            "title": title,
        },
    )
    try:
        doc.save()
    except frappe.QueryDeadlockError:
        doc = frappe.get_doc("Drive Document", doc.name)
        doc.append(
            "versions",
            {
                "snapshot": snapshot,
                "manual": int(manual),
                "title": title,
            },
        )
        doc.save()
    return doc.versions
