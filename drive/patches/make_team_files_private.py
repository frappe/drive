import frappe


def execute():
    """Team files are served through Drive's own access rules, never as public files."""
    frappe.db.set_value("File", {"team": ["is", "set"], "is_private": 0}, "is_private", 1, update_modified=False)
