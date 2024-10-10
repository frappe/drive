# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    get_datetime,
    now,
    split_emails,
    validate_email_address,
)

EXPIRY_DAYS = 1


class DriveUserInvitation(Document):
    def has_expired(self):
        return self.status == "Pending" and get_datetime(self.creation) < get_datetime(
            add_days(now(), -EXPIRY_DAYS)
        )

    def before_insert(self):
        validate_email_address(self.email, True)
        self.key = frappe.generate_hash(length=12)
        self.invited_by = frappe.session.user
        self.status = "Pending"

    def after_insert(self):
        self.invite_via_email()

    def invite_via_email(self):
        invite_link = frappe.utils.get_url(
            f"/api/method/drive.utils.users.accept_invitation?key={self.key}"
        )
        if frappe.local.dev_server:
            print(f"Invite link for {self.email}: {invite_link}")

        title = "Drive"
        template = "drive_invitation"

        frappe.sendmail(
            recipients=self.email,
            subject=f"{title} Invitation",
            template=template,
            args={"title": title, "invite_link": invite_link},
            now=True,
        )
        self.db_set("sent_at", frappe.utils.now())

    @frappe.whitelist()
    def accept_invitation(self):
        frappe.only_for("System Manager")
        self.accept()

    def accept(self):
        if self.has_expired():
            self.db_set("status", "Expired", commit=True)
            frappe.throw("Invalid or expired key")

        if self.status == "Expired":
            frappe.throw("Invalid or expired key")

        if self.status == "Accepted":
            frappe.throw("Invitation already accepted")

        user = self.create_user_if_not_exists()
        user.append_roles(self.role)
        user.save(ignore_permissions=True)

        self.status = "Accepted"
        self.accepted_at = frappe.utils.now()
        self.save(ignore_permissions=True)

    def create_user_if_not_exists(self):
        if not frappe.db.exists("User", self.email):
            first_name = self.email.split("@")[0].title()
            user = frappe.get_doc(
                doctype="User",
                user_type="Website User",
                email=self.email,
                send_welcome_email=0,
                first_name=first_name,
            ).insert(ignore_permissions=True)
        else:
            user = frappe.get_doc("User", self.email)
        return user
