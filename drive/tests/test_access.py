# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.client import insert, save, set_value

from drive.api.activity import get_entity_activity_log
from drive.api.files import (
    create_folder,
    does_entity_exist,
    get_new_title,
    move,
    set_favourite,
    update_access,
)
from drive.api.list import favourites, files
from drive.api.permissions import get_teams, get_user_access
from drive.api.product import create_team, edit_team, leave_team, remove_user, set_user_access
from drive.patches import reset_custom_permissions
from drive.utils import get_default_team
from drive.tests.utils import OTHER, OWNER, THIRD, DriveTestCase, add_member, make_file, make_team, make_user


def names(rows):
    return {r["name"] for r in rows}


def visible_teams():
    try:
        return frappe.get_list("Drive Team", pluck="name")
    except frappe.PermissionError:
        return []


def share(entity_name, **kwargs):
    return update_access(entity_name, "share", cmd="x", **kwargs)


def unshare(entity_name, user):
    return update_access(entity_name, "unshare", cmd="x", user=user)


class TestSharing(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "private.txt", "private")

    def test_editors_with_share_access_can_share_a_file_as_editor(self):
        share(self.file.name, user=OTHER, read=1, comment=1, share=1, write=1)

        # The share dialog sends upload=1 with editor access, for files too
        frappe.set_user(OTHER)
        share(self.file.name, user=THIRD, read=1, comment=1, share=1, upload=1, write=1)
        permission = frappe.db.get_value(
            "Drive Permission", {"entity": self.file.name, "user": THIRD}, ["write", "upload"], as_dict=True
        )
        self.assertEqual((permission.write, permission.upload), (1, 0))

    def test_people_cannot_give_themselves_access(self):
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            insert({"doctype": "Drive Permission", "entity": self.file.name, "user": OTHER, "read": 1})
        self.assertFalse(get_user_access(self.file.name)["read"])

    def test_sharers_cannot_give_more_access_than_they_have(self):
        share(self.file.name, user=OTHER, read=1, share=1)
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            share(self.file.name, user=THIRD, read=1, write=1)
        share(self.file.name, user=THIRD, read=1)
        self.assertFalse(frappe.db.get_value("Drive Permission", {"entity": self.file.name, "user": THIRD}, "write"))

    def test_readers_can_leave_but_not_remove_others(self):
        share(self.file.name, user=OTHER, read=1)
        share(self.file.name, user=THIRD, read=1)
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            unshare(self.file.name, THIRD)
        unshare(self.file.name, OTHER)
        self.assertFalse(frappe.db.exists("Drive Permission", {"entity": self.file.name, "user": OTHER}))
        self.assertTrue(frappe.db.exists("Drive Permission", {"entity": self.file.name, "user": THIRD}))

    def test_only_sharers_see_what_access_other_people_have(self):
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            get_user_access(self.file.name, user=OWNER)
        self.assertFalse(get_user_access(self.file.name, user="Guest")["read"])


class TestFileAccess(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "private.txt", "private")

    def test_guests_and_outsiders_only_find_what_is_shared_with_them(self):
        folder = create_folder(self.team, "Public")
        inside = make_file(self.team, "shared.txt", "hello", parent=folder.name)
        folder.share(user="", read=1)
        for user in ("Guest", OTHER):
            frappe.set_user(user)
            with self.subTest(user=user):
                self.assertEqual(names(files(team="all", entity_name=folder.name)), {inside.name})
                self.assertEqual(names(files(team="all", entity_name=folder.name, search="t")), {inside.name})

    def test_favourites_only_list_readable_files(self):
        share(self.file.name, user=OTHER, read=1)
        frappe.set_user(OTHER)
        set_favourite([{"name": self.file.name, "is_favourite": True}])
        self.assertIn(self.file.name, names(favourites(team="all")))

        frappe.set_user(OWNER)
        unshare(self.file.name, OTHER)
        frappe.set_user(OTHER)
        self.assertNotIn(self.file.name, names(favourites(team="all")))

    def test_folder_upload_checks_from_a_team_root(self):
        # FileUploader.vue sends an empty folder when a folder is uploaded at a team's root or in Home.
        # An error here leaves the upload at "Uploading" forever.
        make_file(self.team, "Photos")
        self.assertEqual(get_new_title("Photos", "", team=self.team), "Photos (1)")

    def test_names_and_activity_need_read_access(self):
        frappe.set_user(OTHER)
        for call in (
            lambda: get_new_title("private.txt", self.home),
            lambda: does_entity_exist("private.txt", self.home),
            lambda: get_entity_activity_log(self.file.name),
        ):
            with self.assertRaises(frappe.PermissionError):
                call()
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list("Drive Entity Activity Log", fields=["message"])

    def test_a_moved_file_joins_its_new_folders_team(self):
        add_member(self.team, OTHER, access_level=2)
        frappe.set_user(OTHER)
        folder = create_folder(self.team, "Archive")
        mine = make_file(self.team, "mine.txt", "mine")
        # The frontend always sends the user's own default team
        move([mine.name], new_parent=folder.name, team=get_default_team())
        stored = frappe.db.get_value("File", mine.name, ["folder", "team"])
        self.assertEqual(stored, (folder.name, self.team))

    def test_moving_needs_write_access_and_upload_access_at_the_destination(self):
        other_team = make_team(OTHER)
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            move([self.file.name], team=other_team)
        frappe.set_user(OWNER)
        with self.assertRaises(frappe.PermissionError):
            move([self.file.name], team=other_team)
        self.assertEqual(frappe.db.get_value("File", self.file.name, "team"), self.team)


class TestTeams(DriveTestCase):
    def test_only_team_admins_can_change_a_team(self):
        add_member(self.team, OTHER)
        for user in (OTHER, THIRD):
            frappe.set_user(user)
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                set_value("Drive Team", self.team, "s3_bucket", "other-bucket")
            team = frappe.get_doc("Drive Team", self.team).as_dict()
            team["users"].append({"user": user, "access_level": 2})
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                save(team)
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                insert({"doctype": "Drive Team", "title": "Mine", "s3_bucket": "other-bucket", "prefix": "x"})
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                edit_team(self.team, team_name="Taken")
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                remove_user(self.team, OWNER)

        frappe.set_user("Administrator")
        team = frappe.get_doc("Drive Team", self.team)
        self.assertFalse(team.s3_bucket)
        self.assertEqual({m.user: m.access_level for m in team.users}, {OWNER: 2, OTHER: 1})

    def test_team_admins_and_members_can_still_manage_a_team(self):
        add_member(self.team, OTHER)
        add_member(self.team, THIRD)

        edit_team(self.team, team_name="Renamed", icon="star")
        set_user_access(self.team, OTHER, 2)
        remove_user(self.team, THIRD)
        frappe.set_user(OTHER)
        leave_team(self.team)

        frappe.set_user("Administrator")
        team = frappe.get_doc("Drive Team", self.team)
        self.assertEqual((team.title, team.icon), ("Renamed", "star"))
        self.assertEqual({m.user for m in team.users}, {OWNER})

    def test_only_drive_admins_choose_where_a_team_is_stored(self):
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            create_team(OTHER, "Elsewhere", s3_bucket="other-bucket", prefix="x")
        team = create_team(OTHER, "Plain")
        self.assertIn(team, get_teams(details=0))

    def test_team_names_cannot_be_paths(self):
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.ValidationError):
            create_team(OTHER, "../../Elsewhere")

    def test_teams_are_hidden_from_people_outside_them(self):
        add_member(self.team, OTHER)
        outsider = make_user(f"drive-outsider-{frappe.generate_hash(length=6)}@test.io")
        for user in ("Guest", outsider):
            frappe.set_user(user)
            with self.subTest(user=user):
                self.assertNotIn(self.team, visible_teams())
                self.assertFalse(frappe.has_permission("Drive Team", "read", self.team))

        frappe.set_user(OTHER)
        self.assertEqual(set(visible_teams()), set(get_teams()))

    def test_teams_list_is_always_the_current_users(self):
        frappe.set_user(OTHER)
        self.assertNotIn(self.team, get_teams(details=1))
        self.assertNotIn(self.team, frappe.call(get_teams, user=OWNER, details=1))

    def test_customised_permissions_are_reset(self):
        frappe.set_user("Administrator")
        for doctype in reset_custom_permissions.DOCTYPES:
            frappe.get_doc(doctype="Custom DocPerm", parent=doctype, role="Drive User", read=1, create=1).insert()
            frappe.clear_cache(doctype=doctype)
        frappe.set_user(OTHER)
        self.assertTrue(frappe.has_permission("Drive User Invitation", "create"))

        frappe.set_user("Administrator")
        reset_custom_permissions.execute()
        reset_custom_permissions.execute()
        frappe.set_user(OTHER)
        for doctype in reset_custom_permissions.DOCTYPES:
            with self.subTest(doctype=doctype):
                self.assertFalse(frappe.has_permission(doctype, "create"))
