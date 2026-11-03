# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import io

import frappe
from werkzeug.datastructures import FileStorage

from drive.api.files import does_entity_exist, get_new_title, get_upload_path, upload_file
from drive.tests.utils import OTHER, OWNER, DriveTestCase, read_file
from drive.utils import get_home_folder


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

    def test_upload_does_not_pick_up_another_uploads_temporary_file(self):
        # A single-request upload of the same name that is still running, or that failed after writing, left this behind
        leftover = get_upload_path(get_home_folder(self.team)["path"], "_report.txt")
        leftover.write_bytes(b"someone else's bytes ")

        upload = self.upload(OTHER, b"mine")
        self.assertEqual(read_file(upload.name), "mine")

    def test_folder_upload_checks_from_a_team_root(self):
        # FileUploader.vue sends an empty folder when a folder is uploaded at a team's root or in Home.
        # An error here leaves the upload at "Uploading" forever.
        frappe.set_user(OTHER)
        self.assertFalse(does_entity_exist("Photos", ""))
        self.assertEqual(get_new_title("Photos", "", folder=True), "Photos")
