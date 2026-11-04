"""Maintenance authorization and storage regressions for an isolated Frappe test site."""

import frappe

from drive.api.files import run_drive_audit, run_drive_repair
from drive.tests.utils import OTHER, OWNER, DriveTestCase, make_file
from drive.utils.files import FileManager


class TestMaintenance(DriveTestCase):
    def test_guests_and_file_owners_cannot_run_site_maintenance(self):
        for user in ("Guest", OWNER, OTHER):
            frappe.set_user(user)
            for call in (run_drive_audit, run_drive_repair):
                with self.subTest(user=user, action=call.__name__), self.assertRaises(frappe.PermissionError):
                    call()

    def test_admin_audits_without_writing_then_repairs_only_the_database_path(self):
        entity = make_file(self.team, "report.txt", "my report")
        canonical = entity.path
        old_path = canonical + ".missing"
        frappe.db.set_value("Drive File", entity.name, "path", old_path)

        frappe.set_user("Administrator")
        report = run_drive_audit()
        row = next(row for row in report["results"] if row["name"] == entity.name)
        self.assertEqual(row["status"], "repairable")
        self.assertEqual(frappe.db.get_value("Drive File", entity.name, "path"), old_path)

        run_drive_repair()
        self.assertEqual(frappe.db.get_value("Drive File", entity.name, "path"), canonical)
        self.assertEqual(FileManager().resolve(canonical).read_text(), "my report")

    def test_admin_does_not_claim_another_records_file(self):
        first = make_file(self.team, "first.txt", "first")
        second = make_file(self.team, "second.txt", "second")
        frappe.db.set_value("Drive File", second.name, {"title": first.title, "path": second.path + ".missing"})
        frappe.set_user("Administrator")
        report = run_drive_repair()
        row = next(row for row in report["results"] if row["name"] == second.name)
        self.assertEqual(row["status"], "invalid")
        self.assertEqual(FileManager().resolve(first.path).read_text(), "first")
