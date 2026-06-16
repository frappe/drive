import frappe


def execute():
    """Ensure the FULLTEXT index used by search exists on migrated sites."""
    index_check = frappe.db.sql(
        """SHOW INDEX FROM `tabFile` WHERE Key_name = 'drive_file_name_fts_idx'"""
    )
    if not index_check:
        frappe.db.sql(
            """ALTER TABLE `tabFile` ADD FULLTEXT INDEX drive_file_name_fts_idx (file_name)"""
        )
