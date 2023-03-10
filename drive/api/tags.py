import frappe


@frappe.whitelist()
def create_tag(title, color="gray"):
    """
    Create new tag for entity

    :param title: Tag name
    :param color: Tag color
    """

    doc = frappe.get_doc({
        'doctype': 'Drive Tag',
        'title': title,
        'color': color,
    })
    doc.insert()

    return doc.name


@frappe.whitelist()
def add_tag(entity, tag):
    """
    Add tag to entity

    :param entity: Entity name
    :param tag: Tag name
    """

    entity = frappe.get_doc('Drive Entity', entity)
    entity.append('tags', {'tag': tag})
    entity.save()


@frappe.whitelist()
def get_entity_tags(entity):
    """
    Add tag to entity

    :param entity: Entity name
    :param tag: Tag name
    """

    entity = frappe.get_doc('Drive Entity', entity)

    return map(lambda x: frappe.db.get_value(
        'Drive Tag', x.tag, ['title', 'color'], as_dict=1), entity.tags)
