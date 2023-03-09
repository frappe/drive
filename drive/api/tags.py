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
        'user': frappe.session.user,
    })
    doc.insert()
