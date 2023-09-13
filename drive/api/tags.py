import frappe


@frappe.whitelist()
def create_tag(title, color="gray"):
    """
    Create new tag for entity

    :param title: Tag name
    :param color: Tag color
    """

    title_lower = title.lower()

    doc = frappe.get_doc(
        {
            "doctype": "Drive Tag",
            "title": title_lower,
            "color": color,
        }
    )

    tag_exists = frappe.db.exists(
        {"doctype": "Drive Tag", "owner": frappe.session.user, "title": title_lower}
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

    doc = frappe.get_doc("Drive Entity", entity)
    doc.append("tags", {"tag": tag})
    doc.save()


@frappe.whitelist()
def get_entity_tags(entity):
    """
    Returns all tags of given entity

    :param entity: Entity name
    """

    entity = frappe.get_doc("Drive Entity", entity)

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
        filters={"owner": frappe.session.user},
        fields=["name", "title", "color"],
    )


@frappe.whitelist()
def update_tag_color(tag, color):
    """
    Update color for givent tag

    :param tag: Tag name
    :param color: Color to be update with
    """

    doc = frappe.get_doc("Drive Tag", tag)
    doc.color = color
    doc.save()


@frappe.whitelist()
def remove_tag(entity, tag):
    """
    Remove tag from entity

    :param entity: Entity name
    :param tag: Tag name
    """

    entity_doc = frappe.get_doc("Drive Entity", entity)
    for tag_doc in entity_doc.tags:
        if tag_doc.tag == tag and tag_doc.owner == frappe.session.user:
            tag_doc.delete(ignore_permissions=True)


@frappe.whitelist()
def delete_tag(tag):
    """
    Delete tag

    :param tag: Tag name
    """

    frappe.delete_doc("Drive Tag", tag)
