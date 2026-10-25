# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from urllib.parse import parse_qs, urlsplit

import frappe
from frappe.client import insert

from drive.api.product import accept_invite, get_my_invites, get_team_invites, invite_users, reject_invite, signup
from drive.tests.utils import OTHER, THIRD, DriveTestCase, make_file


def new_email():
    return f"drive-new-{frappe.generate_hash(length=6)}@test.io"


class TestInvitations(DriveTestCase):
    def setUp(self):
        super().setUp()
        invite_users(OTHER, team=self.team)
        self.key = frappe.db.get_value("Drive User Invitation", {"email": OTHER, "team": self.team}, "name")
        frappe.local.response = frappe._dict()

    def members(self):
        return {m.user for m in frappe.get_doc("Drive Team", self.team).users}

    def status(self, key=None):
        return frappe.db.get_value("Drive User Invitation", key or self.key, "status")

    def test_people_cannot_see_or_create_invitations_directly(self):
        frappe.set_user(THIRD)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list("Drive User Invitation", fields=["name", "email"])
        with self.assertRaises(frappe.PermissionError):
            insert({"doctype": "Drive User Invitation", "email": THIRD, "team": self.team, "status": "Pending"})
        with self.assertRaises(frappe.PermissionError):
            get_team_invites(self.team)

    def test_invitees_see_their_own_invitations(self):
        frappe.set_user(OTHER)
        self.assertIn(self.key, [i.name for i in get_my_invites()])

    def test_only_team_admins_can_invite(self):
        email = new_email()
        frappe.set_user(THIRD)
        for team in (self.team, None):
            with self.subTest(team=team), self.assertRaises(frappe.PermissionError):
                invite_users(email, team=team)
        self.assertFalse(frappe.db.exists("Drive User Invitation", {"email": email}))

    def test_sharing_a_file_with_a_new_email_invites_them(self):
        email = new_email()
        make_file(self.team, "notes.txt").share(email, read=1)
        self.assertEqual(frappe.db.get_value("Drive User Invitation", {"email": email}, "status"), "Automatic")

    def test_a_guest_is_sent_to_log_in_and_is_never_logged_in(self):
        frappe.set_user("Guest")
        accept_invite(self.key)
        self.assertEqual(frappe.session.user, "Guest")
        self.assertTrue(frappe.local.response["location"].startswith("/login?redirect-to="))
        self.assertEqual(self.status(), "Pending")
        self.assertNotIn(OTHER, self.members())

    def test_a_new_person_signs_up_once_from_their_invitation(self):
        email = new_email()
        invite_users(email, team=self.team)
        key = frappe.db.get_value("Drive User Invitation", {"email": email, "team": self.team})
        frappe.set_user("Guest")
        accept_invite(key)
        request = parse_qs(urlsplit(frappe.local.response["location"]).query)["r"][0]
        self.assertEqual(frappe.session.user, "Guest")

        frappe.local.login_manager = frappe._dict(login_as=lambda user: None)
        signup(request, "New", "a-Strong-passw0rd!")
        self.assertIn(email, self.members())
        self.assertEqual(self.status(key), "Accepted")

        frappe.set_user("Guest")
        with self.assertRaises(frappe.ValidationError):
            signup(request, "Again", "a-Strong-passw0rd!")

    def test_new_people_are_only_sent_on_to_paths_on_this_site(self):
        email = new_email()
        invite_users(email, team=self.team)
        key = frappe.db.get_value("Drive User Invitation", {"email": email, "team": self.team})
        frappe.set_user("Guest")
        cases = {"/drive/t/x": True, "https://example.com": False, "//example.com": False, "/\\example.com": False}
        for redirect, kept in cases.items():
            frappe.local.response = frappe._dict()
            accept_invite(key, redirect=redirect)
            with self.subTest(redirect=redirect):
                self.assertEqual("redirect-to=" in frappe.local.response["location"], kept)

    def test_only_the_invited_person_can_accept(self):
        frappe.set_user(THIRD)
        with self.assertRaises(frappe.PermissionError):
            accept_invite(self.key)
        self.assertNotIn(THIRD, self.members())

        frappe.set_user(OTHER)
        accept_invite(self.key)
        self.assertEqual(self.status(), "Accepted")
        self.assertIn(OTHER, self.members())

    def test_only_the_invited_person_or_a_team_admin_can_decline(self):
        frappe.set_user(THIRD)
        with self.assertRaises(frappe.PermissionError):
            reject_invite(self.key)
        self.assertEqual(self.status(), "Pending")

        frappe.set_user(OTHER)
        reject_invite(self.key)
        self.assertEqual(self.status(), "Expired")

    def test_invited_email_matches_regardless_of_case(self):
        invite_users(THIRD.upper(), team=self.team)
        key = frappe.db.get_value("Drive User Invitation", {"email": THIRD, "team": self.team}, "name")
        frappe.set_user(THIRD)
        accept_invite(key)
        self.assertIn(THIRD, self.members())
