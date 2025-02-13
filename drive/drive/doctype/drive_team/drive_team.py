# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from pathlib import Path
from drive.api.files import get_home_folder


class DriveTeam(Document):
    def on_update(self):
        """Creates the file on disk"""
        d = frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": f"Drive - {self.name}",
                "is_group": 1,
                "team": self.name,
            }
        )
        d.insert()

        user_directory_path = Path(frappe.get_site_path("private/files"), d.name)
        user_directory_path.mkdir()
        d.path = d.name
        d.save()

    def on_trash(self):
        # BROKEN
        frappe.db.delete("Drive File", {"team": self.name})
        d = get_home_folder(self.name)
        user_directory_path = Path(frappe.get_site_path("private/files"), d.path)
        user_directory_path.rmdir()
