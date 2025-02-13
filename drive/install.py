import frappe


def after_install():
    index_check = frappe.db.sql(
        """SHOW INDEX FROM `tabDrive File` WHERE Key_name = 'drive_file_title_fts_idx'"""
    )
    if not index_check:
        frappe.db.sql(
            """ALTER TABLE `tabDrive File` ADD FULLTEXT INDEX drive_file_title_fts_idx (title)"""
        )
