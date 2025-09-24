# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import shutil
from pathlib import Path

import frappe
from frappe.model.document import Document

from drive.api.permissions import get_teams
from drive.api.product import set_settings
from drive.utils import get_home_folder


class DriveTeam(Document):
    def after_insert(self):
        """Creates the file on disk"""
        d = frappe.get_doc(
            {
                "name": self.name,
                "doctype": "Drive File",
                "title": f"Drive - {self.name}",
                "path": "",
                "is_group": 1,
                "team": self.name,
            }
        )
        d.insert()

        self.append("users", {"user": frappe.session.user, "access_level": 2})
        self.save()

        settings = frappe.get_single("Drive Disk Settings")
        root_folder: str
        if self.s3_bucket:
            root_folder = self.prefix or ""
        else:
            root_folder = (
                Path(settings.root_folder)
                / {
                    settings.team_prefix == "team_id": self.name + "/",
                    settings.team_prefix == "team_name": f"{self.title} ({frappe.session.user})/",
                    settings.team_prefix == "none": "",
                }[True]
            )
        d.path = str(root_folder)
        d.save()

        # Create even with S3 as we need local folders before uploading to S3
        user_directory_path = Path(frappe.get_site_path("private/files")) / root_folder
        user_directory_path.mkdir(exist_ok=True, parents=True)  # allows prefixes to be nested
        (user_directory_path / ".uploads").mkdir(exist_ok=True)
        (user_directory_path / settings.thumbnail_prefix).mkdir(exist_ok=True)
        if settings.flat:
            (user_directory_path / "embeds").mkdir(exist_ok=True)

    def on_trash(self):
        user_settings = frappe.get_list("Drive Settings", {"default_team": self.name}, pluck=["name"])
        for s in user_settings:
            d = frappe.get_doc("Drive Settings", s)
            d.default_team = ""
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
