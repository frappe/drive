# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, random_string

from drive.utils.users import generate_otp, get_country_info

# from press.utils.telemetry import capture


class AccountRequest(Document):
    def before_insert(self):
        # if not is_valid_email_address(self.email):
        #     frappe.throw(f"{self.email} is not a valid email address")
        self.request_key = random_string(32)

        self.ip_address = frappe.local.request_ip
        geo_location = get_country_info() or {}
        self.geo_location = json.dumps(geo_location, indent=1, sort_keys=True)
        self.state = geo_location.get("regionName")

    def validate(self):
        self.email = self.email.strip()

    def after_insert(self):
        if not self.invite:
            self.set_otp()
            self.send_otp()
        # Telemetry: Only capture if it's not a saas signup or invited by parent team. Also don't capture if user already have a team
        # if not (
        #     frappe.db.exists("Team", {"user": self.email})
        #     or self.is_saas_signup()
        #     or self.invited_by_parent_team
        # ):
        #     # Telemetry: Account Request Created
        #     capture("account_request_created", "fc_signup", self.email)

        # if self.is_saas_signup() and self.is_using_new_saas_flow():
        #     # Telemetry: Account Request Created
        #     capture("account_request_created", "fc_saas", self.email)

        # if self.is_saas_signup() and not self.is_using_new_saas_flow():
        #     # If user used oauth, we don't need to verification email but to track the event in stat, send this dummy event
        #     capture("verification_email_sent", "fc_signup", self.email)
        #     capture("clicked_verify_link", "fc_signup", self.email)

    def set_otp(self):
        self.otp = generate_otp()
        self.otp_generated_at = frappe.utils.now_datetime()
        self.save(ignore_permissions=True)

    def send_otp(self):
        frappe.sendmail(
            recipients=self.email,
            subject="Frappe Drive - OTP",
            template="otp",
            args={"otp": self.otp},
            now=True,
        )

    # if self.oauth_signup:
    #     # Telemetry: simulate verification email sent
    #     capture("verification_email_sent", "fc_signup", self.email)

    def too_many_requests_with_field(self, field_name, limits):
        key = getattr(self, field_name)
        for allowed_count, kwargs in limits:
            count = frappe.db.count(
                self.doctype,
                {field_name: key, "creation": (">", frappe.utils.add_to_date(None, **kwargs))},
            )
            if count > allowed_count:
                return True
        return False

    def get_verification_url(self):
        if self.saas:
            return get_url(
                f"/api/method/press.api.saas.validate_account_request?key={self.request_key}"
            )
        if self.product_trial:
            return get_url(
                f"/dashboard/saas/{self.product_trial}/oauth?key={self.request_key}&email={self.email}"
            )
        return get_url(f"/dashboard/setup-account/{self.request_key}")

    @property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.last_name]))

    def get_site_name(self):
        return self.subdomain + "." + frappe.db.get_value("Saas Settings", self.saas_app, "domain")

    def is_using_new_saas_flow(self):
        return bool(self.product_trial)

    def is_saas_signup(self):
        return bool(self.saas_app or self.saas or self.erpnext or self.product_trial)
