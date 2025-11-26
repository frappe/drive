from frappe.core.doctype.file.file import File
from frappe.model.naming import make_autoname


class DriveFile(File):
    def autoname(self):
        if self.flags.drive_file:
            self.name = make_autoname("hash")
