import frappe


def after_install():
    if frappe.db.db_type == "mariadb":
        index_check = frappe.db.sql("""
            SHOW INDEX FROM `tabDrive File`
            WHERE Key_name = 'drive_file_title_fts_idx'
        """)
        if not index_check:
            frappe.db.sql("""
                ALTER TABLE `tabDrive File`
                ADD FULLTEXT INDEX drive_file_title_fts_idx (title)
            """)
    else:
        # PostgreSQL
        index_check = frappe.db.sql("""
            SELECT 1
            FROM pg_indexes
            WHERE indexname = 'drive_file_title_fts_idx'
        """)
        if not index_check:
            frappe.db.sql("""
                CREATE INDEX drive_file_title_fts_idx
                ON "tabDrive File"
                USING GIN (to_tsvector('simple', title))
            """)
