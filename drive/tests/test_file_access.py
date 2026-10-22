# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from drive.api.files import create_folder, move
from drive.api.list import files
from drive.tests.utils import OTHER, OWNER, DriveTestCase, make_file, make_team
from drive.utils import get_home_folder


def names(rows):
    return {r["name"] for r in rows}


class TestListFiles(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "private.txt", "secret")

    def test_guests_cannot_list_everything(self):
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            files(team="all", only_parent=0)

    def test_everywhere_only_lists_the_users_teams(self):
        make_team(OTHER)
        frappe.set_user(OTHER)
        self.assertNotIn(self.file.name, names(files(team="all", only_parent=0)))
        frappe.set_user(OWNER)
        self.assertIn(self.file.name, names(files(team="all", only_parent=0)))

    def test_guests_can_still_open_a_public_folder(self):
        folder = create_folder(self.team, "Public")
        inside = make_file(self.team, "shared.txt", "hello", parent=folder.name)
        folder.share(user="", read=1)
        frappe.set_user("Guest")
        self.assertEqual(names(files(team=None, entity_name=folder.name)), {inside.name})


class TestMove(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "report.txt", "numbers")
        self.other_team = make_team(OTHER)

    def test_cannot_move_files_without_write_access(self):
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            move([self.file.name], team=self.other_team)
        self.assertEqual(frappe.db.get_value("Drive File", self.file.name, "team"), self.team)

    def test_cannot_move_into_a_folder_without_upload_access(self):
        with self.assertRaises(frappe.PermissionError):
            move([self.file.name], new_parent=get_home_folder(self.other_team)["name"])

    def test_owner_can_move_into_their_folder(self):
        folder = create_folder(self.team, "Archive")
        move([self.file.name], new_parent=folder.name, team=self.other_team)
        moved = frappe.db.get_value("Drive File", self.file.name, ["parent_entity", "team"], as_dict=True)
        # The team always follows the folder
        self.assertEqual((moved.parent_entity, moved.team), (folder.name, self.team))
