import frappe


@frappe.whitelist()
def convert_pm_to_md(obj):
    from pmconverter import prose2markdown

    return prose2markdown(obj)


@frappe.whitelist()
def get_yjs_content(entity_name):
    return frappe.get_value("Drive Document", frappe.get_value("Drive File", entity_name, "document"), "content")


from markdownify import markdownify as md

import time


@frappe.whitelist()
def sync_to_wiki_page(wiki_space, group, entity_name, html):
    title = frappe.get_value("Drive File", entity_name, "title")
    content = md(html)
    route = group.lower().replace(" ", "-") + "/" + title.lower().replace(" ", "-")
    existing_page = frappe.db.exists("Wiki Page", {"route": route})

    if existing_page:
        frappe.get_doc("Wiki Page", existing_page).update({"content": content}).save()
        return
        # frappe.delete_doc("Wiki Page", existing_page)
        # time.sleep(0.5)

    page = frappe.get_doc(
        {
            "doctype": "Wiki Page",
            "title": title,
            "route": route,
            "wiki_space": wiki_space,
            "content": content,
            "published": 1,
        }
    )
    page.insert()

    return page.name


@frappe.whitelist()
def add_pages_to_space(wiki_space, group, pages):
    space = frappe.get_doc("Wiki Space", wiki_space)
    for page in pages:
        space.append("wiki_sidebars", {"parent_label": group, "wiki_page": page})
    space.save()


@frappe.whitelist()
def sync_space(folder, wiki_space):
    # Get all groups (subfolders) and pages (nested documents) in this folder
    groups = frappe.get_all(
        "Drive File",
        filters={"parent_entity": folder, "is_group": 1, "is_active": 1},
        fields=["name", "title"],
    )
    res = {}
    for g in groups:
        res[g.title] = frappe.get_all(
            "Drive File",
            filters={"parent_entity": g.name},
            pluck="name",
        )
    return frappe.publish_realtime("sync_to_wiki", {"space": wiki_space, "groups": res})
