# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from urllib.parse import parse_qs, urlsplit

import frappe

from drive.api.product import accept_invite, get_team_invites, invite_users, reject_invite, signup
from drive.drive.doctype.drive_user_invitation.drive_user_invitation import get_invite_link
from drive.tests.utils import OTHER, DriveTestCase, make_file, make_user

THIRD = "drive-third@test.io"


class TestInvitations(DriveTestCase):
    def setUp(self):
        super().setUp()
        make_user(THIRD)
        invite_users(OTHER, team=self.team)
        self.key = frappe.db.get_value("Drive User Invitation", {"email": OTHER, "team": self.team}, "name")
        frappe.local.response = frappe._dict()

    def members(self):
        return {m.user for m in frappe.get_doc("Drive Team", self.team).users}

    def status(self):
        return frappe.db.get_value("Drive User Invitation", self.key, "status")

    def test_users_cannot_list_other_peoples_invitations(self):
        frappe.set_user(THIRD)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_list("Drive User Invitation", fields=["name", "email"])
        with self.assertRaises(frappe.PermissionError):
            get_team_invites(self.team)

    def test_only_team_admins_can_invite(self):
        email = f"drive-new-{frappe.generate_hash(length=6)}@test.io"
        frappe.set_user(THIRD)
        for team in (self.team, None):
            with self.subTest(team=team), self.assertRaises(frappe.PermissionError):
                invite_users(email, team=team)
        self.assertFalse(frappe.db.exists("Drive User Invitation", {"email": email}))

    def test_sharing_a_file_with_a_new_email_invites_them(self):
        email = f"drive-new-{frappe.generate_hash(length=6)}@test.io"
        make_file(self.team, "notes.txt").share(email, read=1)
        self.assertEqual(frappe.db.get_value("Drive User Invitation", {"email": email}, "status"), "Automatic")

    def test_a_guest_is_sent_to_log_in_and_is_never_logged_in(self):
        frappe.set_user("Guest")
        accept_invite(self.key)
        self.assertEqual(frappe.session.user, "Guest")
        self.assertTrue(frappe.local.response["location"].startswith("/drive/login?redirect-to="))
        self.assertEqual(self.status(), "Pending")
        self.assertNotIn(OTHER, self.members())

    def test_new_users_are_only_sent_on_to_paths_on_this_site(self):
        email = f"drive-new-{frappe.generate_hash(length=6)}@test.io"
        invite_users(email, team=self.team)
        key = frappe.db.get_value("Drive User Invitation", {"email": email, "team": self.team})
        token = parse_qs(urlsplit(get_invite_link(key)).query)["token"][0]
        frappe.set_user("Guest")
        cases = {"/drive/t/x": True, "https://example.com": False, "//example.com": False, "/\\example.com": False}
        for redirect, kept in cases.items():
            frappe.local.response = frappe._dict()
            accept_invite(key, redirect=redirect, token=token)
            with self.subTest(redirect=redirect):
                self.assertEqual("redirect-to=" in frappe.local.response["location"], kept)

    def test_only_the_invited_user_can_accept(self):
        frappe.set_user(THIRD)
        with self.assertRaises(frappe.PermissionError):
            accept_invite(self.key)
        frappe.set_user(OTHER)
        accept_invite(self.key)
        self.assertEqual(self.status(), "Accepted")
        self.assertIn(OTHER, self.members())

    def test_only_the_invited_user_or_an_admin_can_reject(self):
        frappe.set_user(THIRD)
        with self.assertRaises(frappe.PermissionError):
            reject_invite(self.key)
        frappe.set_user(OTHER)
        reject_invite(self.key)
        self.assertEqual(self.status(), "Expired")

    def test_invited_email_matches_regardless_of_case(self):
        invite_users(THIRD.upper(), team=self.team)
        key = frappe.db.get_value("Drive User Invitation", {"email": THIRD, "team": self.team}, "name")
        frappe.set_user(THIRD)
        accept_invite(key)
        self.assertIn(THIRD, self.members())

    def test_new_people_sign_up_only_from_the_emailed_link(self):
        email = f"drive-new-{frappe.generate_hash(length=6)}@test.io"
        invite_users(email, team=self.team)
        key = frappe.db.get_value("Drive User Invitation", {"email": email, "team": self.team})
        link = urlsplit(get_invite_link(key))
        frappe.set_user("Guest")
        for token in (None, "0" * 64):
            with self.subTest(token=token), self.assertRaises(frappe.PermissionError):
                accept_invite(key, token=token)
        self.assertFalse(frappe.db.exists("Account Request", {"email": email}))

        accept_invite(**{k: v[0] for k, v in parse_qs(link.query).items()})
        request = parse_qs(urlsplit(frappe.local.response["location"]).query)["r"][0]
        frappe.local.login_manager = frappe._dict(login_as=frappe.set_user)
        signup(request, "New")
        self.assertIn(email, self.members())
        self.assertEqual(self.status_of(key), "Accepted")

    def status_of(self, key):
        return frappe.db.get_value("Drive User Invitation", key, "status")
