# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from drive.api.product import signup, verify_otp

EMAIL = "drive-otp@test.io"


class TestVerifyOtp(IntegrationTestCase):
    def setUp(self):
        frappe.local.request_ip = "127.0.0.1"
        self.req = frappe.get_doc({"doctype": "Account Request", "email": EMAIL}).insert(ignore_permissions=True)
        self.req.set_otp()
        self.otp = str(self.req.otp)

    def tearDown(self):
        frappe.set_user("Administrator")

    def verify(self, otp):
        # The rate limiter would trip after a few calls
        with patch("frappe.rate_limiter.RateLimiter.apply"):
            verify_otp(self.req.name, otp)

    def test_correct_otp_is_accepted_once(self):
        self.verify(self.otp)
        self.assertEqual(frappe.db.get_value("Account Request", self.req.name, "login_count"), 1)
        with self.assertRaises(frappe.ValidationError):
            self.verify(self.otp)

    def test_wrong_otp_is_rejected(self):
        wrong = "100000" if self.otp != "100000" else "100001"
        with self.assertRaises(frappe.ValidationError):
            self.verify(wrong)

    def test_expired_otp_is_rejected(self):
        frappe.db.set_value(
            "Account Request", self.req.name, "otp_generated_at", add_to_date(now_datetime(), minutes=-11)
        )
        with self.assertRaises(frappe.ValidationError):
            self.verify(self.otp)

    def test_signup_needs_a_verified_email_and_works_once(self):
        frappe.db.set_single_value("Website Settings", "disable_signup", 0)
        frappe.set_user("Guest")
        with self.assertRaises(frappe.ValidationError):
            signup(self.req.name, "Otp", "a-Strong-passw0rd!")

        self.verify(self.otp)
        frappe.local.login_manager = frappe._dict(login_as=lambda user: None)
        signup(self.req.name, "Otp", "a-Strong-passw0rd!")
        self.assertTrue(frappe.db.exists("User", EMAIL))

        frappe.db.delete("User", EMAIL)
        with self.assertRaises(frappe.ValidationError):
            signup(self.req.name, "Otp", "a-Strong-passw0rd!")
        self.assertFalse(frappe.db.exists("User", EMAIL))


class TestCountryInfo(IntegrationTestCase):
    def test_no_lookup_unless_enabled(self):
        from drive.utils.users import get_country_info

        frappe.local.request_ip = "203.0.113.1"
        with patch("drive.utils.users.requests.get") as get:
            self.assertEqual(get_country_info(), {})
            get.assert_not_called()
