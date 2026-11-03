# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from drive.api.embed import get_file_content as get_embed_content
from drive.api.files import (
    create_document_entity,
    create_folder,
    create_link,
    edit_file_content,
    get_file_content,
    remove_or_restore,
    stream_file_content,
)
from drive.tests.utils import OTHER, OWNER, DriveTestCase, make_file, make_team, read_file
from drive.utils.files import FileManager


class TestLinks(DriveTestCase):
    def test_links_are_saved_as_web_addresses(self):
        self.assertEqual(create_link(self.team, "Docs", "example.com/docs").path, "https://example.com/docs")
        self.assertEqual(create_link(self.team, "Site", "http://example.com").path, "http://example.com")
        for link in ("file:///tmp/notes.txt", "ftp://example.com/notes.txt", "https://"):
            with self.subTest(link=link), self.assertRaises(frappe.ValidationError):
                create_link(self.team, "Other", link)

    def test_links_are_in_their_folders_team(self):
        other_team = make_team(OTHER)
        folder = create_folder(self.team, "Bookmarks")
        link = create_link(other_team, "Docs", "example.com", parent=folder.name)
        self.assertEqual(link.team, self.team)

    def test_links_never_read_or_change_files_on_disk(self):
        # Older links could have any path, including another team's file
        frappe.set_user(OTHER)
        notes = make_file(make_team(OTHER), "notes.txt", "hello")
        frappe.set_user(OWNER)
        document = create_document_entity(self.team)
        links = [
            create_link(self.team, "Notes", "example.com"),
            create_link(self.team, "Notes", "example.com", document.name),
        ]
        for link in links:
            frappe.db.set_value("Drive File", link.name, "path", notes.path)

        frappe.local.request = frappe._dict(headers={})
        self.addCleanup(lambda: setattr(frappe.local, "request", None))
        reads = {
            "download": lambda link: get_file_content(link.name),
            "stream": lambda link: stream_file_content(link.name),
            "embed": lambda link: get_embed_content(link.name, document.name),
            "edit": lambda link: edit_file_content(link.name),
        }
        for action, read in reads.items():
            with self.subTest(action=action), self.assertRaises((frappe.ValidationError, frappe.NotFound)):
                read(links[1] if action == "embed" else links[0])

        link = frappe.get_doc("Drive File", links[0].name)
        link.rename("Renamed")
        remove_or_restore([link.name])
        remove_or_restore([link.name])
        self.assertTrue((FileManager().site_folder / notes.path).exists())
        self.assertEqual(read_file(notes.name), "hello")
