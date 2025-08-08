import frappe


def execute():
    settings = frappe.get_single("Drive Disk Settings")
    settings.flat = True
    settings.save()
