# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from drive.api.notifications import create_notification, get_link
from drive.utils import extract_mentions


class DriveComment(Document):
    @frappe.whitelist()
    def edit(self, content):
        self.content = content
        self.save()

    def after_insert(self):
        """
        Does not create a notification until it's mentioned
        Always notifies owner for fresh comments
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
            create_notification(
                self.owner,
                mention,
                "Mention",
                doc,
                f"{from_owner} mentioned you in a comment in {doc.title}",
            )
            frappe.sendmail(
                recipients=[mention],
                subject=f"Frappe Drive - Comment in {doc.title}",
                template="drive_comment",
                args={
                    "message": f'{from_owner} mentioned you in a comment.',
                    "doc": doc.title, 
                    "link": get_link(doc),
                },
                now=True,
            )
