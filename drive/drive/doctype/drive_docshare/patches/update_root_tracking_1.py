import frappe
from frappe.utils import cint


def execute():
    all_docshares = frappe.get_all("Drive DocShare", fields="*")
    for docshare in all_docshares:
        entity = frappe.get_doc("Drive Entity", docshare.share_name)
        if frappe.db.exists(
            {
                "doctype": "Drive DocShare",
                "share_doctype": "Drive Entity",
                "share_name": entity.parent_drive_entity,
                "everyone": cint(docshare.everyone),
                "public": cint(docshare.public),
                "user_name": docshare.user,
                "user_doctype": docshare.user_type,
            }
        ):
            parent_docshare = frappe.db.get_value(
                "Drive DocShare",
                {
                    "share_doctype": "Drive Entity",
                    "share_name": entity.parent_drive_entity,
                    "everyone": cint(docshare.everyone),
                    "public": cint(docshare.public),
                    "user_name": docshare.user,
                    "user_doctype": docshare.user_type,
                },
                "name",
            )
            docshare.update({"owner_parent": parent_docshare, "share_parent": parent_docshare})
    pass
