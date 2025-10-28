# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from drive.utils.files import FileManager
from drive.utils import get_default_team


class DriveTransfer(Document):
    def after_delete(self):
        if self.path:
            FileManager().delete_file(frappe._dict(**self.as_dict(), team=get_default_team()))
