# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import shutil
from pathlib import Path

import frappe
from frappe.model.document import Document

from drive.utils import get_home_folder


class DriveTeam(Document):
    def on_update(self):
        """Creates the file on disk"""
        DriveFile = frappe.qb.DocType("Drive File")
        if (
            frappe.qb.from_(DriveFile)
            .where(((DriveFile.team == self.name) & DriveFile.parent_entity.isnull()))
            .select(DriveFile.name, DriveFile.path)
            .run(as_dict=True)
        ):
            return
        d = frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": f"Drive - {self.name}",
                "is_group": 1,
                "team": self.name,
            }
        )
        d.insert()

        settings = frappe.get_single("Drive Disk Settings")
        user_directory_path = (
            Path(frappe.get_site_path("private/files"))
            / {
                settings.root_prefix_type == "team_id": d.name,
                settings.root_prefix_type == "team_name": self.title,
                settings.root_prefix_type == "other": settings.root_prefix_value,
            }[True]
        )
        user_directory_path.mkdir()

        if settings.flat:
            (user_directory_path / "uploads").mkdir()
            (user_directory_path / "embeds").mkdir()
            (user_directory_path / "thumbnails").mkdir()
        else:
            (user_directory_path / settings.team_prefix).mkdir(exist_ok=True)
            (user_directory_path / settings.team_prefix).mkdir(exist_ok=True)
        d.path = d.name
        d.save()

    def on_trash(self):
        try:
            d = get_home_folder(self.name)
            user_directory_path = Path(frappe.get_site_path("private/files"), d.path)
            shutil.rmtree(str(user_directory_path))
        except FileNotFoundError:
            pass
        frappe.db.delete("Drive File", {"team": self.name})
        frappe.db.commit()
