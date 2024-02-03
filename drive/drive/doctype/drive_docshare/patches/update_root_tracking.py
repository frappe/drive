import frappe


def execute():
    # Update existing docshare based on parent_shares
    all_docshares = frappe.get_all("Drive DocShare", fields=["name", "share_name"])
    for docshare in all_docshares:
        entity = frappe.get_doc("Drive Entity", docshare.share_name)
        entity.share()
    pass
