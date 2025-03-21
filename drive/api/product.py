import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import escape_html


def check_invites(doc, method=None):
    invites = frappe.db.get_list(
        "Drive User Invitation",
        filters={"email": doc.email, "status": "Pending"},
        pluck="name",
        ignore_permissions=True,
    )
    if not invites:
        # Create team for this user
        frappe.local.login_manager.login_as(doc.email)
        team = frappe.get_doc(
            {
                "doctype": "Drive Team",
                "title": "Personal",
            },
        )
        team.insert(ignore_permissions=True)
        team.append("users", {"user": doc.email, "is_admin": 1})
        team.save()
        frappe.local.response["location"] = "/drive/" + team.name
    else:
        for invite_name in invites:
            invite = frappe.get_doc("Drive User Invitation", invite_name)

            invite.accept()


CORPORATE_DOMAINS = ["gmail.com", "icloud.com", "frappemail.com"]


@frappe.whitelist(allow_guest=True)
def signup(
    account_request, first_name, last_name, password, invite_key=None, team=None, referrer=None
):
    account_request = frappe.get_doc("Account Request", account_request)
    if not account_request.login_count:
        frappe.throw("Email not verified")
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": account_request.email,
            "first_name": escape_html(first_name),
            "last_name": escape_html(last_name),
            "enabled": 1,
            "new_password": password,
            "user_type": "Website User",
        }
    )
    user.flags.ignore_permissions = True
    user.flags.ignore_password_policy = True
    try:
        user.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        frappe.throw("User already exists")
    account_request.signed_up = 1
    account_request.save(ignore_permissions=True)
    frappe.local.login_manager.login_as(user.email)

    # Check invites for this user
    valid_invite = frappe.db.exists(
        "Drive User Invitation", {"name": invite_key, "status": "Pending"}
    )
    if valid_invite:
        pass
    else:
        # Create team for this user
        team = frappe.get_doc(
            {
                "doctype": "Drive Team",
                "title": "Your Drive",
            },
        ).insert(ignore_permissions=True)
        team.append("users", {"user": user.email, "is_admin": 1})
        team.save()
        frappe.local.response["location"] = "/drive/t/" + team.name


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def send_otp(email):
    is_login = frappe.db.exists(
        "Account Request",
        {
            "email": email,
            "signed_up": 1,
        },
    )
    if not is_login:
        account_request = frappe.get_doc(
            {
                "doctype": "Account Request",
                "email": email,
            }
        ).insert(ignore_permissions=True)
        return account_request.name
    else:
        req = frappe.get_doc("Account Request", is_login, ignore_permissions=True)
        req.set_otp()
        req.send_otp()
        return is_login


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def verify_otp(account_request, otp):
    req = frappe.get_doc("Account Request", account_request)
    if req.otp != otp:
        frappe.throw("Invalid OTP")
    req.login_count += 1
    req.save(ignore_permissions=True)
    if req.signed_up:
        frappe.local.login_manager.login_as(req.email)
        return {"location": "/drive"}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def resend_otp(email):
    account_request = frappe.db.get_value("Account Request", {"email": email}, "name")
    if not account_request:
        frappe.get_doc(
            {
                "doctype": "Account Request",
                "email": email,
                "send_email": True,
            }
        )

    account_request = frappe.get_doc("Account Request", account_request)

    # if last OTP was sent less than 30 seconds ago, throw an error
    if (
        account_request.otp_generated_at
        and (frappe.utils.now_datetime() - account_request.otp_generated_at).seconds < 30
    ):
        frappe.throw("Please wait for 30 seconds before requesting a new OTP")

    account_request.reset_otp()
    account_request.send_login_mail()
