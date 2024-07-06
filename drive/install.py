import frappe


def after_install():
    frappe.db.sql(
        """ALTER TABLE `Drive Entity` ADD FULLTEXT INDEX drive_entity_title_fts_idx (title)"""
    )
