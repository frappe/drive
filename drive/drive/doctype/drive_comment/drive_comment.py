# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from drive.api.notifications import create_notification
from drive.utils.files import extract_mentions


class DriveComment(Document):
    @frappe.whitelist()
    def edit(self, content):
        self.content = content
        self.save()

    def after_insert(self):
        """
        Does not create a notification until it's mentioned
        """
        mentions = extract_mentions(self.content)
        if not mentions:
            return

        from_owner = frappe.get_cached_value("User", self.owner, "full_name")

        try:
            doc = frappe.get_doc("Drive File", self.parent)
        except:
            doc = frappe.get_doc("Drive File", self.parent_doc.parent)

        for mention in mentions:
            print(doc, from_owner)
            create_notification(
                self.owner,
                mention,
                "Mention",
                doc,
                f"{from_owner} mentioned you in a comment in {doc.title}",
            )
