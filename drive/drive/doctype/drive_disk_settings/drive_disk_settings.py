# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DriveDiskSettings(Document):
    def __getattribute__(self, attr):
        """
        We want explicit denial of , so require '/' at the DB level.
        However, this causes a lot of problems with `Path`, so override empty prefixes.
        """
        val = object.__getattribute__(self, attr)
        if attr == "root_prefix_value":
            return val if val != "/" else ""
        return val
