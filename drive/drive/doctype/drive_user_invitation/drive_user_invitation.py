# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import hashlib
import hmac
from urllib.parse import quote

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, get_datetime, now, validate_email_address
from frappe.utils.password import get_encryption_key

EXPIRY_DAYS = 1


class DriveUserInvitation(Document):
    def has_expired(self):
        return get_datetime(self.creation) < get_datetime(add_days(now(), -EXPIRY_DAYS))

    def before_insert(self):
        validate_email_address(self.email, True)
        # User IDs are lowercase emails
        self.email = self.email.strip().lower()

    def after_insert(self):
        if self.status == "Pending":
            try:
                self.invite_via_email()
            except BaseException as e:
                frappe.log_error(f"Failed to send invite email: {e}")
                pass
        elif self.status == "Proposed":
            admins = frappe.get_all("Drive Team Member", filters={"parent": self.team, "access_level": 2}, pluck="user")
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
                "invite_link": get_invite_link(self.name),
                "user": frappe.session.user,
                "team_name": frappe.db.get_value("Drive Team", self.team, "title"),
            },
            now=True,
        )

    def accept(self, redirect=True, token=None):
        """
        Add the invited person to the team.

        Never logs anyone in. A guest is sent to log in, or to sign up, as the invited email first.
        """
        if self.status not in ["Pending", "Automatic"]:
            frappe.throw("This key has already been used")
        if self.status == "Expired" or self.has_expired():
            self.status = "Expired"
            self.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.throw("Invalid or expired key")

        if redirect:
            frappe.local.response["type"] = "redirect"

        if frappe.session.user == "Guest":
            return self.send_guest_to_login(redirect, token)
        if frappe.session.user != self.email.lower():
            frappe.throw(f"This invitation is for {self.email}. Please log in with that account.", frappe.PermissionError)

        if self.team:
            team = frappe.get_doc("Drive Team", self.team)
            email = self.email.lower()
            if email not in {member.user for member in team.users}:
                team.append("users", {"user": email, "access_level": 0 if self.as_guest else 1})
                team.save(ignore_permissions=True)
        self.status = "Accepted"
        self.accepted_on = frappe.utils.now()
        self.save(ignore_permissions=True)
        frappe.db.commit()

        location = f"/drive/t/{self.team}" if self.team else "/drive"
        frappe.local.response["location"] = location
        return location

    def send_guest_to_login(self, redirect, token=None):
        if frappe.db.exists("User", self.email):
            # Come back to this link once logged in as the invited user
            accept_url = f"/api/method/drive.api.product.accept_invite?key={self.name}"
            frappe.local.response["location"] = f"/login?redirect-to={quote(accept_url)}"
            return

        # Only the emailed link has the token, so it stands in for verifying the email when signing up
        if not token or not hmac.compare_digest(str(token), get_invite_token(self.name)):
            frappe.throw("Please open the link in your invitation email to sign up.", frappe.PermissionError)
        req = frappe.get_doc(
            {
                "doctype": "Account Request",
                "email": self.email,
                "invite": self.name,
                "login_count": 1,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        team_name = frappe.db.get_value("Drive Team", self.team, "title")
        url = f"/drive/signup?e={quote(self.email)}{'&t=' + quote(team_name) if team_name else ''}&r={req.name}"
        if isinstance(redirect, str) and is_site_path(redirect):
            url += f"&redirect-to={quote(redirect)}"
        frappe.local.response["location"] = url


def get_invite_token(key):
    return hmac.new(get_encryption_key().encode(), f"Drive User Invitation {key}".encode(), hashlib.sha256).hexdigest()


def get_invite_link(key, redirect=None):
    """The link emailed to an invited person. Its token shows that whoever opens it received the email."""
    url = f"/api/method/drive.api.product.accept_invite?key={key}&token={get_invite_token(key)}"
    if redirect:
        url += f"&redirect={quote(redirect)}"
    return frappe.utils.get_url(url)


def is_site_path(path):
    """True for a path on this site such as "/drive". Browsers treat "//host" and "/\\host" as other sites."""
    return path.startswith("/") and path[1:2] not in ("/", "\\") and path.isprintable()
