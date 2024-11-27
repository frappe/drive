import frappe

def after_install():
    index_check = frappe.db.sql(
        """SHOW INDEX FROM `tabDrive Entity` WHERE Key_name = 'drive_entity_title_fts_idx'"""
    )
    if not index_check:
        frappe.db.sql(
            """ALTER TABLE `tabDrive Entity` ADD FULLTEXT INDEX drive_entity_title_fts_idx (title)"""
        )
