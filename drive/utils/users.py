import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import now, split_emails, validate_email_address
import requests
import os


@frappe.whitelist()
def get_all_users(team):
    team_users = {k.user: k.is_admin for k in frappe.get_doc("Drive Team", team).users}
    users = frappe.get_all(
        doctype="User",
        filters=[
            ["name", "in", list(team_users.keys())],
        ],
        fields=[
            "name",
            "email",
            "full_name",
            "user_image",
        ],
    )
    for u in users:
        u["role"] = "admin" if team_users[u["name"]] else "user"
    return users


@frappe.whitelist()
def invite_users(team, emails):
    if not emails:
        return

    email_string = validate_email_address(emails, throw=False)
    email_list = split_emails(email_string)
    if not email_list:
        return

    existing_invites = frappe.db.get_list(
        "Drive User Invitation",
        filters={"email": ["in", email_list], "team": team},
        pluck="email",
    )

    new_invites = list(set(email_list) - set(existing_invites))
    for email in new_invites:
        invite = frappe.new_doc("Drive User Invitation")
        invite.email = email
        invite.team = team
        invite.insert()


@frappe.whitelist()
def set_role(team, user_id, role):
    if not is_admin(team):
        frappe.throw("You don't have the permissions for this action.")
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    drive_team[user_id].is_admin = role
    drive_team[user_id].save()


@frappe.whitelist()
def is_admin(team):
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    return drive_team[frappe.session.user].is_admin


@frappe.whitelist()
def remove_user(team, user_id):
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    if frappe.session.user not in drive_team:
        frappe.throw("User doesn't belong to team")
    frappe.delete_doc("Drive Team Member", drive_team[user_id].name)


def mark_as_viewed(entity):
    if frappe.session.user == "Guest":
        return
    if not frappe.has_permission(
        doctype="Drive Entity Log", ptype="write", user=frappe.session.user
    ):
        return
    if entity.is_group:
        return
    entity_name = entity.name
    entity_log = frappe.db.get_value(
        "Drive Entity Log", {"entity_name": entity_name, "user": frappe.session.user}
    )
    if entity_log:
        frappe.db.set_value(
            "Drive Entity Log", entity_log, "last_interaction", now(), update_modified=False
        )
        return
    doc = frappe.new_doc("Drive Entity Log")
    doc.entity_name = entity_name
    doc.user = frappe.session.user
    doc.last_interaction = now()
    doc.insert()
    return doc


@frappe.whitelist(allow_guest=True)
def accept_invitation(key):
    try:
        invitation = frappe.get_doc("Drive User Invitation", key)
    except:
        frappe.throw("Invalid or expired key")

    return invitation.accept()


@frappe.whitelist(allow_guest=True)
@rate_limit(key="reference_name", limit=10, seconds=60 * 60)
def add_comment(reference_name: str, content: str, comment_email: str, comment_by: str):
    """Allow logged user with permission to read document to add a comment"""
    exists = frappe.db.exists("Drive File", reference_name)
    if not exists:
        frappe.throw("Entity does not exist", frappe.NotFound)
    comment = frappe.new_doc("Comment")
    comment.update(
        {
            "comment_type": "Comment",
            "reference_doctype": "Drive File",
            "reference_name": reference_name,
            "comment_email": comment_email,
            "comment_by": comment_by,
            "content": content,
        }
    )
    comment.insert(ignore_permissions=True)
    return comment


def generate_otp():
    """Generates a cryptographically secure random OTP"""

    return int.from_bytes(os.urandom(5), byteorder="big") % 900000 + 100000


def get_country_info():
    ip = frappe.local.request_ip

    def _get_country_info():
        fields = [
            "status",
            "message",
            "continent",
            "continentCode",
            "country",
            "countryCode",
            "region",
            "regionName",
            "city",
            "district",
            "zip",
            "lat",
            "lon",
            "timezone",
            "offset",
            "currency",
            "isp",
            "org",
            "as",
            "asname",
            "reverse",
            "mobile",
            "proxy",
            "hosting",
            "query",
        ]

        res = requests.get(f"https://pro.ip-api.com/json/{ip}?fields={",".join(fields)}")
        try:
            data = res.json()
            if data.get("status") != "fail":
                return data
        except Exception:
            pass

        return {}

    return frappe.cache().hget("ip_country_map", ip, generator=_get_country_info)
