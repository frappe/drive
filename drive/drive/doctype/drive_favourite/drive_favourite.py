# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from drive.api.permissions import user_has_permission
from frappe.model.document import Document
import frappe


class DriveFavourite(Document):
    def validate(self):
        """
        Users can only create favourite files they can access.
        """
        if frappe.session.user not in ["Administrator", self.user]:
            raise frappe.PermissionError("You can only create favourites for yourself.")

        file = frappe.get_doc("File", self.entity)
        if not user_has_permission(file, "read"):
            raise frappe.PermissionError("You cannot favourite this file.")
