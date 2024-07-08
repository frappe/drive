# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DriveNotification(Document):
    def before_save(self):
        if frappe.db.exists(
            {
                "doctype": "Drive Notification",
                "from_user": self.from_user,
                "to_user": self.to_user,
                "type": self.type,
                "notif_doctype_name": self.notif_doctype_name,
            }
        ):
            frappe.throw("Duplicate Notification")
