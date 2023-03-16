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
    Returns all tags of given entity

    :param entity: Entity name
    """

    entity = frappe.get_doc('Drive Entity', entity)

    return map(lambda x: frappe.db.get_value(
        'Drive Tag', x.tag, ['name', 'title', 'color'], as_dict=1), entity.tags)


@frappe.whitelist()
def get_user_tags():
    """
    Returns all tags created by current user

    """

    return frappe.db.get_list('Drive Tag',
                              filters={
                                  'owner': frappe.session.user
                              },
                              fields=['name', 'title', 'color'],
                              )


@frappe.whitelist()
def update_tag_color(tag, color):
    """
    Returns all tags created by current user

    """

    doc = frappe.get_doc('Drive Tag', tag)
    doc.color = color
    doc.save()
