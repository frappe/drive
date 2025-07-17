# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime


class DriveComment(Document):
    @frappe.whitelist()
    def edit(self, content):
        self.content = content
        self.save()
