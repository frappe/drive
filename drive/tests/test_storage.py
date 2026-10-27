# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
import os

import frappe
from frappe.client import insert, save, set_value
from frappe.core.doctype.file.file import File as FrappeFile
from frappe.core.doctype.file.utils import find_file_by_url
from frappe.handler import run_doc_method

from drive.api.files import (
    create_folder,
    create_link,
    get_file_content,
    get_upload_path,
    move,
    rename,
    stream_file_content,
    upload_file,
)
from drive.tests.utils import (
    OTHER,
    OWNER,
    DriveTestCase,
    add_member,
    attach_upload,
    disk_path,
    make_file,
    make_team,
    read_file,
)
from drive.utils.files import FileManager

OUTSIDE_URL = "/private/files/../../../../drive-outside.txt"


class TestStorageFields(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "note.md", "hello")

    def test_owner_cannot_change_where_a_file_points(self):
        other_team = make_team(OTHER)
        theirs = make_file(other_team, "theirs.txt", "theirs")
        changes = (
            ("file_url", OUTSIDE_URL),
            ("file_url", theirs.file_url),
            ("team", other_team),
            ("folder", theirs.folder),
            ("file_name", "../renamed.md"),
            ("file_size", -(10**12)),
        )
        for field, value in changes:
            with self.subTest(field=field, value=value), self.assertRaises(frappe.PermissionError):
                set_value("File", self.file.name, field, value)
        doc = frappe.get_doc("File", self.file.name).as_dict()
        doc["file_url"] = theirs.file_url
        with self.assertRaises(frappe.PermissionError):
            save(doc)
        self.assertEqual(read_file(self.file.name), "hello")

    def test_drive_files_cannot_be_created_through_generic_apis(self):
        theirs = make_file(make_team(OTHER), "theirs.txt", "theirs")
        for file_url in (theirs.file_url, OUTSIDE_URL):
            with self.subTest(file_url=file_url), self.assertRaises(frappe.PermissionError):
                insert(
                    {
                        "doctype": "File",
                        "file_name": "copy.txt",
                        "team": self.team,
                        "folder": self.home,
                        "file_url": file_url,
                        "is_private": 1,
                    }
                )

    def test_links_are_web_addresses_only(self):
        other_team = make_team(OTHER)
        frappe.set_user(OTHER)
        theirs = make_file(other_team, "theirs.txt", "theirs")
        frappe.set_user(OWNER)
        for link in (theirs.file_url, "/api/method/drive.api.files.get_file_content", "file:///etc/passwd"):
            with self.subTest(link=link), self.assertRaises(frappe.ValidationError):
                create_link(self.team, "link", link)

        self.assertEqual(create_link(self.team, "site", "example.com").file_url, "https://example.com")

        # Links saved by older versions never serve the bytes their address names
        old_link = create_link(self.team, "old", "https://example.com")
        frappe.db.set_value("File", old_link.name, {"file_url": theirs.file_url, "is_private": 0})
        frappe.set_user(OWNER)
        self.assertIsNone(find_file_by_url(theirs.file_url))
        with self.assertRaises(frappe.PermissionError):
            FrappeFile.zip_files([old_link.name])
        with self.assertRaises(frappe.PermissionError):
            insert({"doctype": "File", "file_name": "copy.txt", "file_url": theirs.file_url, "is_private": 1})

    def test_file_methods_are_not_callable_as_document_methods(self):
        frappe.get_doc("File", self.file.name).share(OTHER, read=1)
        frappe.set_user(OTHER)
        edited = frappe.get_doc("File", self.file.name).as_dict()
        edited.update(owner=OTHER, modified=str(edited.modified), creation=str(edited.creation))
        calls = (
            ("rename", {"docs": json.dumps(edited, default=str), "args": {"new_file_name": "mine.md"}}),
            ("share", {"dt": "File", "dn": self.file.name, "args": {"user": OTHER, "write": 1}}),
            ("unshare", {"dt": "File", "dn": self.file.name, "args": {"user": OWNER}}),
        )
        for method, params in calls:
            with self.subTest(method=method), self.assertRaises(frappe.PermissionError):
                run_doc_method(method, **params)
        stored = frappe.db.get_value("File", self.file.name, ["file_name", "owner"])
        self.assertEqual(stored, ("note.md", OWNER))

    def test_drive_can_still_rename_and_move(self):
        folder = create_folder(self.team, "Folder")
        rename(self.file.name, "renamed.md")
        move([self.file.name], new_parent=folder.name)
        stored = frappe.db.get_value("File", self.file.name, ["file_name", "folder"])
        self.assertEqual(stored, ("renamed.md", folder.name))
        self.assertEqual(read_file(self.file.name), "hello")

    def test_names_that_are_paths_are_refused(self):
        for name in ("../renamed.md", "a/b.md", "..", "."):
            with self.subTest(name=name), self.assertRaises(frappe.ValidationError):
                rename(self.file.name, name)
            with self.subTest(name=name), self.assertRaises(frappe.ValidationError):
                create_folder(self.team, name)
        self.assertEqual(read_file(self.file.name), "hello")

    def test_stored_paths_outside_storage_are_never_opened(self):
        # A path stored by an earlier version
        frappe.db.set_value("File", self.file.name, "file_url", OUTSIDE_URL)
        frappe.local.request = frappe._dict(headers={}, environ={})
        with self.assertRaises(frappe.PermissionError):
            get_file_content(self.file.name)

        frappe.local.request = frappe._dict(headers={"Range": "bytes=0-"}, environ={})
        frappe.db.set_value("File", self.file.name, "file_type", "Video")
        with self.assertRaises(frappe.PermissionError):
            stream_file_content(self.file.name)

    def test_links_inside_storage_that_lead_outside_are_never_followed(self):
        outside = os.path.realpath(frappe.get_site_path("site_config.json"))
        path = disk_path(self.file.name)
        path.unlink()
        path.symlink_to(outside)
        frappe.local.request = frappe._dict(headers={}, environ={})
        with self.assertRaises(frappe.PermissionError):
            get_file_content(self.file.name)

    def test_absolute_paths_are_refused(self):
        with self.assertRaises(frappe.PermissionError):
            FileManager().resolve("/etc/passwd")


class TestUploads(DriveTestCase):
    def upload(self, content=b"content", filename="report.txt", **form):
        attach_upload(content, filename, **form)
        return upload_file(team=self.team, total_file_size=len(content))

    def test_upload_session_ids_stay_inside_the_uploads_folder(self):
        outside = frappe.get_site_path("private", "drive-upload-session_report.txt")
        # The size is never reached, so the call returns after writing the first chunk
        attach_upload(uuid="../../drive-upload-session")
        upload_file(team=self.team, total_file_size=999999)
        self.assertFalse(os.path.exists(outside))

    def test_uploaded_names_cannot_leave_their_folder(self):
        for filename in ("../../outside.txt", ".."):
            with self.subTest(filename=filename), self.assertRaises(frappe.ValidationError):
                self.upload(filename=filename)
        self.assertFalse(os.path.exists(frappe.get_site_path("private", "outside.txt")))

    def test_upload_does_not_pick_up_another_uploads_temporary_file(self):
        # A single-request upload of the same name that is still running, or that failed after writing, left this behind
        get_upload_path("_report.txt").write_bytes(b"someone else's bytes ")
        upload = self.upload(b"mine")
        self.assertEqual(read_file(upload.name), "mine")

    def test_same_name_uploads_by_two_members_keep_both(self):
        add_member(self.team, OTHER)
        first = self.upload(b"first")
        frappe.set_user(OTHER)
        second = self.upload(b"second")
        self.assertEqual(second.file_name, "report (1).txt")
        self.assertEqual(read_file(first.name), "first")
        self.assertEqual(read_file(second.name), "second")
