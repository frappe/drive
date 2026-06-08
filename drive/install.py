import frappe


def after_install():
    index_check = frappe.db.sql(
        """SHOW INDEX FROM `tabFile` WHERE Key_name = 'drive_file_name_fts_idx'"""
    )
    if not index_check:
        frappe.db.sql(
            """ALTER TABLE `tabFile` ADD FULLTEXT INDEX drive_file_name_fts_idx (file_name)"""
        )
