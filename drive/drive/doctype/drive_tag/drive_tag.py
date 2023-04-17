# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from drive.api.tags import remove_tag


class DriveTag(Document):
    def on_trash(self):
        drive_entities = frappe.db.get_list(
            "Drive Entity", filters={"owner": self.owner}, pluck="name"
        )

        for entity in drive_entities:
            remove_tag(entity, self.name)
