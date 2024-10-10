import frappe


all_entities = frappe.db.get_list("Drive Entity", fields=["name", "title", "owner", "creation"])

for i in all_entities:
    doc = frappe.get_doc(
        {
            "doctype": "Drive Entity Activity Log",
            "entity": i.name,
            "action_type": "create",
            "message": f"Created {i.title}",
            "owner": i.owner,
        }
    )
    doc.insert()
    frappe.db.set_value("Drive Entity Activity Log", doc.name, "creation", i.creation)

