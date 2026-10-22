# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import io

import frappe
from werkzeug.datastructures import FileStorage

from drive.api.files import upload_file
from drive.tests.utils import OTHER, OWNER, DriveTestCase, read_file


class TestUploads(DriveTestCase):
    def setUp(self):
        super().setUp()
        team = frappe.get_doc("Drive Team", self.team)
        team.append("users", {"user": OTHER, "access_level": 1})
        team.save(ignore_permissions=True)

    def upload(self, user, content):
        frappe.set_user(user)
        frappe.local.form_dict = frappe._dict()
        frappe.local.request = frappe._dict(
            files={"file": FileStorage(stream=io.BytesIO(content), filename="report.txt")}
        )
        return upload_file(team=self.team, total_file_size=str(len(content)))

    def test_same_name_uploads_by_two_members_keep_both(self):
        first = self.upload(OWNER, b"first")
        second = self.upload(OTHER, b"second")

        self.assertEqual(second.title, "report (1).txt")
        self.assertEqual(read_file(first.name), "first")
        self.assertEqual(read_file(second.name), "second")
