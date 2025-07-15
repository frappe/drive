# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    get_datetime,
    now,
    validate_email_address,
)

EXPIRY_DAYS = 1


class DriveUserInvitation(Document):
    def has_expired(self):
        return False
        return get_datetime(self.creation) < get_datetime(add_days(now(), -EXPIRY_DAYS))

    def before_insert(self):
        validate_email_address(self.email, True)

    def after_insert(self):
        if self.status == "Pending":
            self.invite_via_email()
        elif self.status == "Proposed":
            admins = frappe.get_all(
                "Drive Team Member", filters={"parent": self.team, "access_level": 2}, pluck="user"
            )
            for admin in admins:
                frappe.get_doc(
                    {
                        "doctype": "Drive Notification",
                        "to_user": admin,
                        "type": "Team",
                        "message": f"A person ({self.email}) from your domain has joined Frappe Drive",
                    }
                ).insert(ignore_permissions=True)
            frappe.db.commit()

    def invite_via_email(self):
        frappe.sendmail(
            recipients=self.email,
            subject=f"Frappe Drive - Invitation",
            template="drive_invitation",
            args={
                "invite_link": frappe.utils.get_url(
                    f"/api/method/drive.api.product.accept_invite?key={self.name}"
                ),
                "user": frappe.session.user,
                "team_name": frappe.db.get_value("Drive Team", self.team, "title"),
            },
            now=True,
        )

    def accept(self, redirect=True):
        if self.status != "Pending":
            frappe.throw("This key has already been used")
        if self.status == "Expired" or self.has_expired():
            self.status = "Expired"
            self.save(ignore_permissions=True)
            frappe.throw("Invalid or expired key")

        exists = frappe.db.exists(
            "Account Request",
            {
                "email": self.email,
                "signed_up": 1,
            },
        )

        if redirect:
            frappe.local.response["type"] = "redirect"

        if not exists:
            # If the user does not have an account, redirect to sign up
            req = frappe.get_doc(
                {
                    "doctype": "Account Request",
                    "email": self.email,
                    "invite": self.name,
                    "login_count": 1,
                }
            ).insert(ignore_permissions=True)
            frappe.db.commit()
            user_exists = frappe.db.exists("User", self.email)

            if not user_exists:
                url = f"/drive/signup?e={self.email}&t={frappe.db.get_value('Drive Team', self.team, 'title')}&r={req.name}"
                frappe.local.response["location"] = url
                return

        # Otherwise, add the user to the team
        team = frappe.get_doc("Drive Team", self.team)
        team.append("users", {"user": self.email})
        team.save(ignore_permissions=True)
        self.status = "Accepted"
        self.accepted_at = frappe.utils.now()
        self.save(ignore_permissions=True)
        frappe.db.commit()

        if frappe.session.user == "Guest":
            frappe.local.login_manager.login_as(self.email)

        frappe.local.response["location"] = "/drive/t/" + self.team
        return "/drive/t/" + self.team
