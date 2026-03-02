# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import annotations

import json

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, random_string

from drive.utils.users import generate_otp, get_country_info


class AccountRequest(Document):
    def before_insert(self):
        self.request_key = random_string(32)

        self.ip_address = frappe.local.request_ip
        geo_location = get_country_info() or {}
        self.geo_location = json.dumps(geo_location, indent=1, sort_keys=True)
        self.state = geo_location.get("regionName")

    def validate(self):
        self.email = self.email.strip()

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

    @property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.last_name]))
