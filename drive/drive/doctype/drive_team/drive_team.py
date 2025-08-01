# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import shutil
from pathlib import Path

import frappe
from frappe.model.document import Document

from drive.utils import get_home_folder


class DriveTeam(Document):
    def after_insert(self):
        """Creates the file on disk"""
        d = frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": f"Drive - {self.name}",
                "is_group": 1,
                "team": self.name,
            }
        )
        # Could lead to colissions in the future, but makes life so much easier
        d.name = self.name
        d.insert()

        self.append("users", {"user": frappe.session.user, "access_level": 2})
        self.save()

        settings = frappe.get_single("Drive Disk Settings")
        root_folder = {
            settings.root_prefix_type == "team_id": d.name,
            settings.root_prefix_type == "team_name": self.title,
            settings.root_prefix_type
            == "other": settings.root_prefix_value if settings.root_prefix_value != "/" else "",
        }[True]
        d.path = root_folder
        d.save()

        # Create even with S3 as we need local folders before uploading to S3
        user_directory_path = Path(frappe.get_site_path("private/files")) / root_folder
        user_directory_path.mkdir(exist_ok=True, parents=True)  # allows prefixes to be nested
        (user_directory_path / "uploads").mkdir(exist_ok=True)
        (user_directory_path / settings.thumbnail_prefix).mkdir(exist_ok=True)
        if settings.flat:
            (user_directory_path / "embeds").mkdir(exist_ok=True)
        else:
            (user_directory_path / settings.team_prefix).mkdir(exist_ok=True)
            (user_directory_path / settings.personal_prefix).mkdir(exist_ok=True)

    def on_trash(self):
        user_settings = frappe.get_list(
            "Drive Settings", {"default_team": self.name}, pluck=["name"]
        )
        for s in user_settings:
            d = frappe.get_doc("Drive Settings", s)
            d.default_team = ""
            print(d.name, d.default_team)
            d.save()
        frappe.db.commit()

        try:
            files_dir = Path(frappe.get_site_path("private/files"))
            user_directory_path = files_dir / get_home_folder(self.name).path
            if user_directory_path != files_dir:
                shutil.rmtree(str(user_directory_path))
            frappe.db.delete("Drive File", {"team": self.name})
        except:
            pass
