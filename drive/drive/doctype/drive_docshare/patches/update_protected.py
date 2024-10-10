import frappe


def execute():
    all_shares = frappe.db.get_list(
        "Drive DocShare",
        fields=[
            "share_name",
            "user_doctype",
            "user_name",
            "creation",
            "everyone",
            "public",
            "read",
            "write",
            "owner",
            "share_parent",
            "owner_parent",
            "protected",
            "name",
        ],
        filters=[
            ["share_parent", "is", "not set"],
            ["owner_parent", "is", "not set"],
            ["user_doctype", "=", "User"],
            ["protected", "=", False],
        ],
    )

    for index, value in enumerate(all_shares):
        entity = frappe.get_doc("Drive Entity", value.share_name)
        parent_entities = []
        while entity.parent_drive_entity:
            parent_entities.append(entity.owner)
            entity = frappe.get_doc("Drive Entity", entity.parent_drive_entity)
        parent_entities = parent_entities[::-1]
        if parent_entities[0] != parent_entities[-1]:
            if value.user_name == parent_entities[0]:
                frappe.db.set_value("Drive DocShare", value.name, "protected", 1)
