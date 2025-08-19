# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DriveTrash(Document):
    def validate(self):
        """Kiểm tra entity có tồn tại và thuộc về team được chỉ định"""
        if not frappe.db.exists("Drive File", self.entity):
            frappe.throw(f"File {self.entity} không tồn tại")
        
        entity_team = frappe.db.get_value("Drive File", self.entity, "team")
        if entity_team != self.team:
            frappe.throw(f"Team của file không khớp: {entity_team} != {self.team}")

    def before_insert(self):
        """Đặt giá trị trashed_on bằng thời gian hiện tại nếu chưa có"""
        if not self.trashed_on:
            self.trashed_on = frappe.utils.now()


