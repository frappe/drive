from frappe.core.doctype.file.file import File
from frappe.model.naming import make_autoname


class DriveFile(File):
    def autoname(self):
        self.name = make_autoname("hash")
