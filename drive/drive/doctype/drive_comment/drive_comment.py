# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
from frappe.model.document import Document


class DriveComment(Document):
    @frappe.whitelist()
    def edit(self, content):
        self.content = content
        self.save()
