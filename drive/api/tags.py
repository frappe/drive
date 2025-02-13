import frappe


@frappe.whitelist()
def create_tag(title, color="gray"):
    """
    Create new tag for entity

    :param title: Tag name
    :param color: Tag color
    """

    doc = frappe.get_doc(
        {
            "doctype": "Drive Tag",
            "title": title,
            "color": color,
        }
    )

    tag_exists = frappe.db.exists(
        {"doctype": "Drive Tag", "owner": frappe.session.user, "title": title}
    )
    if tag_exists:
        frappe.throw("Tag already exists")
    doc.save()
    return doc.name


@frappe.whitelist()
def add_tag(entity, tag):
    """
    Add tag to entity

    :param entity: Entity name
    :param tag: Tag name
    """
    doc = frappe.get_doc("Drive File", entity)
    doc.append("tags", {"tag": tag})
    doc.save()


@frappe.whitelist()
def get_entity_tags(entity):
    """
    Returns all tags of given entity

    :param entity: Entity name
    """

    entity = frappe.get_doc("Drive File", entity)

    return map(
        lambda x: frappe.db.get_value("Drive Tag", x.tag, ["name", "title", "color"], as_dict=1),
        entity.tags,
    )


@frappe.whitelist()
def get_user_tags():
    """
    Returns all tags created by current user

    """
    return frappe.db.get_list(
        "Drive Tag",
        fields=["name", "title", "color"],
    )


@frappe.whitelist()
def get_tags_with_owner():
    """
    Returns all tags created by current user

    """
    return frappe.db.get_list(
        "Drive Tag",
        fields=["name", "title", "color", "owner"],
        as_list=False,
    )


@frappe.whitelist()
def edit_tag(tag, title, color):
    """
    Update color for givent tag

    :param tag: Tag name
    :param color: Color to be update with
    """
    doc = frappe.get_doc("Drive Tag", tag)
    doc.title = title
    doc.color = color
    doc.save()


@frappe.whitelist()
def remove_tag(entity, tag=None, all=False):
    """
    Remove tag from entity

    :param entity: Entity name
    :param tag: Tag name
    """

    entity_doc = frappe.get_doc("Drive File", entity)
    for tag_doc in entity_doc.tags:
        if (tag_doc.tag == tag or all) and tag_doc.owner == frappe.session.user:
            tag_doc.delete(ignore_permissions=True)


@frappe.whitelist()
def delete_tag(tag):
    """
    Delete tag

    :param tag: Tag name
    """
    EntityTag = frappe.qb.DocType("Drive File Tag")
    query = frappe.qb.from_(EntityTag).select(EntityTag.name).where(EntityTag.tag == tag)
    result = query.run(as_dict=True)
    for i in result:
        frappe.delete_doc("Drive File Tag", i.name)
    frappe.delete_doc("Drive Tag", tag)
    return result
