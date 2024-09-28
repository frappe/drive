# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from drive.api.storage import add_new_site_config_key


class DriveInstanceSettings(Document):
    def before_save(self):
        add_new_site_config_key("max_storage", self.self_storage_limit)
