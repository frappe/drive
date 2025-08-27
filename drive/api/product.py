import json
import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import escape_html
from frappe.utils import split_emails, validate_email_address
from drive.api.permissions import is_admin
from frappe.translate import get_all_translations
import re
import csv
import os
from raven.raven_bot.doctype.raven_bot.raven_bot import RavenBot


CORPORATE_DOMAINS = ["gmail.com", "icloud.com", "frappemail.com"]


def access_app():
    return True


@frappe.whitelist()
def get_domain_teams(domain):
    return frappe.db.get_all(
        "Drive Team", filters={"team_domain": ["like", "%" + domain]}, fields=["name", "title"]
    )


@frappe.whitelist()
def create_personal_team(email=frappe.session.user, team_name=None):
    """
    Used for creating teams, personal or not.
    """
    team = frappe.get_doc(
        {
            "doctype": "Drive Team",
            "title": team_name if team_name else "Your Drive",
            "team_domain": email.split("@")[-1] if team_name else "",
        }
    ).insert(ignore_permissions=True)
    team.append("users", {"user": email, "access_level": 2})
    team.save()
    return team.name


@frappe.whitelist()
def request_invite(team, email=None):
    invite = frappe.new_doc("Drive User Invitation")
    invite.email = email or frappe.session.user
    invite.team = team
    invite.status = "Proposed"
    invite.insert(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def get_invites(email):
    invites = frappe.db.get_list(
        "Drive User Invitation",
        fields=["creation", "status", "team", "name"],
        filters={"email": email, "status": ("in", ("Proposed", "Pending"))},
    )
    for i in invites:
        i["team_name"] = frappe.db.get_value("Drive Team", i["team"], "title")
    return invites


@frappe.whitelist()
def get_team_invites(team):
    invites = frappe.db.get_list(
        "Drive User Invitation",
        fields=["creation", "status", "email", "name"],
        filters={"team": team, "status": ("in", ("Proposed", "Pending"))},
    )
    for i in invites:
        i["user_name"] = frappe.db.get_value("User", i["email"], "full_name")
    return invites


@frappe.whitelist(allow_guest=True)
def direct_signup(email, password, first_name, last_name=None, referrer=None):
    """Direct signup with email and password, bypassing account request system"""

    # Validate email format
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        frappe.throw("Invalid email format")

    # Check if user already exists
    if frappe.db.exists("User", email):
        frappe.throw("User already exists")

    # Create user with password
    user = frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": escape_html(first_name),
            "last_name": escape_html(last_name) if last_name else "",
            "enabled": 1,
            "user_type": "Website User",
            "new_password": password,
        }
    )

    user.flags.no_welcome_mail = True
    try:
        user.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        frappe.throw("User already exists")

    # Login the user
    frappe.local.login_manager.login_as(user.email)

    # Create drive settings
    doc = frappe.get_doc(
        {
            "doctype": "Drive Settings",
            "user": email,
            "single_click": 1,
        }
    )
    doc.insert()

    return {"location": "/drive"}


@frappe.whitelist(allow_guest=True)
def signup(account_request, first_name, last_name=None, team=None):
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
            "user_type": "Website User",
        }
    )

    user.flags.no_welcome_mail = True
    user.flags.ignore_password_policy = True
    try:
        user.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        frappe.throw("User already exists")
    account_request.signed_up = 1

    team = None

    if account_request.invite:
        invite = frappe.get_doc("Drive User Invitation", account_request.invite)
        invite.status = "Accepted"
        invite.save(ignore_permissions=True)

        # Add to that team
        team = frappe.get_doc("Drive Team", invite.team)
        team.append("users", {"user": account_request.email})
        team.save(ignore_permissions=True)
        team = invite.team

    account_request.save(ignore_permissions=True)
    frappe.local.login_manager.login_as(user.email)
    doc = frappe.get_doc(
        {
            "doctype": "Drive Settings",
            "user": account_request.email,
            "single_click": 1,
        }
    )
    doc.insert()
    # Check invites for this user
    # if not team:
    #     # Create team for this user
    #     domain = user.email.split("@")[-1]
    #     if domain in CORPORATE_DOMAINS:
    #         team = create_personal_team(user.email)
    #     else:
    #         return get_domain_teams(domain)

    return {"location": "/drive/t/" + team if team else "/drive"}


@frappe.whitelist(allow_guest=True)
def oauth_providers():
    from frappe.utils.html_utils import get_icon_html
    from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
    from frappe.utils.password import get_decrypted_password

    out = []
    providers = frappe.get_all(
        "Social Login Key",
        filters={"enable_social_login": 1},
        fields=["name", "client_id", "base_url", "provider_name", "icon"],
        order_by="name",
    )

    for provider in providers:
        client_secret = get_decrypted_password("Social Login Key", provider.name, "client_secret")
        if not client_secret:
            continue

        icon = None
        if provider.icon:
            if provider.provider_name == "Custom":
                icon = get_icon_html(provider.icon, small=True)
            else:
                icon = f"<img src='{provider.icon}' alt={provider.provider_name}>"

        if provider.client_id and provider.base_url and get_oauth_keys(provider.name):
            auth_url = get_oauth2_authorize_url(provider.name, "/drive")
            out.append(
                {
                    "name": provider.name,
                    "provider_name": provider.provider_name,
                    "auth_url": auth_url,
                    "icon": icon,
                }
            )
    return out


# Legacy OTP functions - Commented out as no longer needed with email/password authentication
# @frappe.whitelist(allow_guest=True)
# @rate_limit(limit=5, seconds=60)
# def send_otp(email, login):
#     is_login = frappe.db.exists(
#         "Account Request",
#         {
#             "email": email,
#             "signed_up": 1,
#         },
#     )
#     if not is_login:
#         if login:
#             frappe.throw("Email account not found!")
#         account_request = frappe.get_doc(
#             {
#                 "doctype": "Account Request",
#                 "email": email,
#             }
#         ).insert(ignore_permissions=True)
#         return account_request.name
#     else:
#         req = frappe.get_doc("Account Request", is_login, ignore_permissions=True)
#         req.set_otp()
#         req.send_otp()
#         return is_login


# @frappe.whitelist(allow_guest=True)
# @rate_limit(limit=5, seconds=60)
# def verify_otp(account_request, otp):
#     req = frappe.get_doc("Account Request", account_request)
#     if req.otp != otp:
#         frappe.throw("Invalid OTP")
#     req.login_count += 1
#     req.save(ignore_permissions=True)
#     if req.signed_up:
#         frappe.local.login_manager.login_as(req.email)
#         return {"location": "/drive"}


@frappe.whitelist(allow_guest=True)
def get_settings():
    if frappe.session.user == "Guest":
        return {}
    try:
        return frappe.get_cached_doc("Drive Settings", frappe.session.user)
    except:
        return {}


@frappe.whitelist()
def set_settings(updates):
    try:
        settings = frappe.get_doc("Drive Settings", frappe.session.user)
    except:
        settings = frappe.get_doc({"doctype": "Drive Settings", "user": frappe.session.user})
        settings.insert()
    if "single_click" in updates:
        settings.single_click = int(updates["single_click"])
    if "auto_detect_links" in updates:
        settings.auto_detect_links = int(updates["auto_detect_links"])
    if "default_team" in updates:
        settings.default_team = updates["default_team"]
    settings.save()


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def resend_otp(email):
    account_request = frappe.db.get_value("Account Request", {"email": email}, "name")
    if not account_request:
        frappe.throw("OTP was never requested.")

    account_request = frappe.get_doc("Account Request", account_request)

    # if last OTP was sent less than 30 seconds ago, throw an error
    if (
        account_request.otp_generated_at
        and (frappe.utils.now_datetime() - account_request.otp_generated_at).seconds < 30
    ):
        frappe.throw("Please wait for 30 seconds before requesting a new OTP")

    account_request.reset_otp()
    account_request.send_login_mail()


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
        filters={"email": ["in", email_list], "team": team, "status": "Pending"},
        pluck="email",
    )

    new_invites = list(set(email_list) - set(existing_invites))
    for email in new_invites:
        invite = frappe.new_doc("Drive User Invitation")
        invite.email = email
        invite.team = team
        invite.status = "Pending"
        invite.insert()


@frappe.whitelist()
def add_user_directly_to_team(team, email, access_level=1):
    """
    Thêm người dùng trực tiếp vào nhóm mà không cần quy trình mời
    """
    from frappe.utils import validate_email_address

    # Kiểm tra email hợp lệ
    if not validate_email_address(email, throw=False):
        frappe.throw("Địa chỉ email không hợp lệ")

    # Kiểm tra người dùng có tồn tại không
    user_exists = frappe.db.exists("User", email)
    if not user_exists:
        frappe.throw("Người dùng không tồn tại trong hệ thống")

    # Kiểm tra người dùng đã trong nhóm chưa
    team_doc = frappe.get_doc("Drive Team", team)
    existing_member = next((member for member in team_doc.users if member.user == email), None)

    if existing_member:
        frappe.throw("Người dùng đã là thành viên của nhóm này")

    # Thêm người dùng vào nhóm
    team_doc.append("users", {"user": email, "access_level": access_level})
    team_doc.save(ignore_permissions=True)

    # Gửi email thông báo
    try:
        # frappe.sendmail(
        #     recipients=[email],
        #     subject=f"Đã được thêm vào nhóm {team_doc.title}",
        #     message=f"""
        #         <p>Xin chào,</p>
        #         <p>Bạn đã được thêm vào nhóm <strong>{team_doc.title}</strong> bởi {frappe.get_value('User', frappe.session.user, 'full_name') or frappe.session.user}.</p>
        #         <p>Bạn có thể truy cập tệp của nhóm và cộng tác với các thành viên khác.</p>
        #         <p><a href="{frappe.utils.get_url()}/drive/t/{team}/team">Truy cập nhóm</a></p>
        #         <p>Trân trọng,<br>Drive Team</p>
        #     """,
        #     now=True,
        # )

        bot_docs = frappe.conf.get("bot_docs")
        if not bot_docs:
            return
        full_name = (
            frappe.get_value("User", frappe.session.user, "full_name") or frappe.session.user
        )
        message_data = {
            "key": "add_user_to_drive_team",
            "title": f'"{full_name}" đã thêm bạn tham gia nhóm "{team_doc.title}"',
            "full_name_owner": full_name,
            "team_name": team_doc.title,
            "link": f"/drive/t/{team}/team",
        }

        RavenBot.send_notification_to_user(
            bot_name=bot_docs,
            user_id=email,
            message=json.dumps(message_data, ensure_ascii=False, default=str),
        )
    except Exception as e:
        frappe.log_error(f"Gửi email thông báo nhóm thất bại: {str(e)}")

    return {"success": True, "message": "Thêm người dùng vào nhóm thành công"}


@frappe.whitelist()
def set_user_access(team, user_id, access_level):
    if not is_admin(team):
        frappe.throw("You don't have the permissions for this action.")
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    drive_team[user_id].access_level = access_level
    drive_team[user_id].save()


@frappe.whitelist()
def remove_user(team, user_id):
    drive_team = {k.user: k for k in frappe.get_doc("Drive Team", team).users}
    if frappe.session.user not in drive_team:
        frappe.throw("User doesn't belong to team")
    frappe.delete_doc("Drive Team Member", drive_team[user_id].name)


@frappe.whitelist()
def get_all_users(team):
    team_users = {k.user: k.access_level for k in frappe.get_doc("Drive Team", team).users}
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
        u["access_level"] = team_users[u["name"]]
    return users


@frappe.whitelist()
def get_all_site_users():
    """Get all users in the site, not just team members"""
    users = frappe.get_all(
        doctype="User",
        filters={
            "enabled": 1,
            "user_type": ("!=", "Website User"),
            "name": ("not in", ("Administrator", "Guest")),
        },
        fields=[
            "name",
            "email",
            "full_name",
            "user_image",
        ],
        order_by="full_name",
    )
    return users


@frappe.whitelist()
def get_system_users():
    """Get all system users for mentions"""
    users = frappe.get_all(
        doctype="User",
        filters=[
            ["user_type", "=", "System User"],
            ["enabled", "=", 1],
            ["name", "!=", "Administrator"],
        ],
        fields=[
            "name",
            "email",
            "full_name",
            "user_image",
        ],
        order_by="full_name asc",
    )
    return users


@frappe.whitelist()
def check_users_permissions(entity_name, user_emails):
    """
    Check if users have read permission for a specific entity
    :param entity_name: Drive File name
    :param user_emails: List of user emails or JSON string
    """
    import json

    if isinstance(user_emails, str):
        user_emails = json.loads(user_emails)

    if not isinstance(user_emails, list):
        user_emails = [user_emails]

    result = []

    for email in user_emails:
        has_permission = False

        try:
            # Check if user has read permission for the entity
            entity_doc = frappe.get_doc("Drive File", entity_name)

            # Check if user is owner
            if entity_doc.owner == email:
                has_permission = True
            else:
                # Check Drive Permission permissions
                share_doc = frappe.db.exists(
                    "Drive Permission", {"entity": entity_name, "user": email}
                )

                if share_doc:
                    share = frappe.get_doc("Drive Permission", share_doc)
                    if share.read == 1:
                        has_permission = True

                # Check if user is in a team that has access
                if not has_permission:
                    # Check team permissions via Drive Permission with team user format
                    team_shares = frappe.get_all(
                        "Drive Permission",
                        {"entity": entity_name, "user": ("like", "$TEAM%"), "read": 1},
                        ["user"],
                    )

                    for team_share in team_shares:
                        # Extract team name from user field (format: $TEAM:team_name)
                        team_name = (
                            team_share.user.replace("$TEAM:", "")
                            if team_share.user.startswith("$TEAM:")
                            else team_share.user
                        )
                        team_members = frappe.get_all(
                            "Drive Team User", {"parent": team_name, "user": email}
                        )
                        if team_members:
                            has_permission = True
                            break

        except Exception as e:
            frappe.log_error(f"Error checking permission for {email}: {str(e)}")
            has_permission = False

        result.append({"email": email, "has_permission": has_permission})

    return result


@frappe.whitelist()
def grant_read_access_to_users(entity_name, user_emails):
    """
    Grant read access to users for a specific entity
    :param entity_name: Drive File name
    :param user_emails: List of user emails or JSON string
    """
    import json

    if isinstance(user_emails, str):
        user_emails = json.loads(user_emails)

    if not isinstance(user_emails, list):
        user_emails = [user_emails]

    results = []

    for email in user_emails:
        try:
            # Check if user exists
            user_exists = frappe.db.exists("User", email)
            if not user_exists:
                results.append({"email": email, "success": False, "error": "User does not exist"})
                continue

            # Check if share already exists using Drive Permission
            existing_share = frappe.db.exists(
                "Drive Permission", {"entity": entity_name, "user": email}
            )

            if existing_share:
                # Update existing share to grant read access
                share_doc = frappe.get_doc("Drive Permission", existing_share)
                share_doc.read = 1
                share_doc.save(ignore_permissions=True)
            else:
                # Create new share with read access using Drive Permission
                share_doc = frappe.new_doc("Drive Permission")
                share_doc.update(
                    {
                        "entity": entity_name,
                        "user": email,
                        "read": 1,
                        "write": 0,
                        "share": 0,
                        "comment": 1,
                    }
                )
                share_doc.insert(ignore_permissions=True)

            results.append(
                {"email": email, "success": True, "message": "Read access granted successfully"}
            )

        except Exception as e:
            frappe.log_error(f"Error granting access to {email}: {str(e)}")
            results.append({"email": email, "success": False, "error": str(e)})

    return results


@frappe.whitelist(allow_guest=True)
def accept_invite(key, redirect=True):
    try:
        invitation = frappe.get_doc("Drive User Invitation", key)
    except:
        frappe.throw("Invalid or expired key")

    return invitation.accept(redirect)


@frappe.whitelist()
def reject_invite(key):
    try:
        invitation = frappe.get_doc("Drive User Invitation", key)
    except:
        frappe.throw("Invalid or expired key")

    invitation.status = "Expired"
    invitation.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def get_translations():
    """Get all translations for the frontend"""
    try:
        # Start with some hardcoded translations for testing
        translations = {
            "Home": "Tài liệu của tôi",
            "Search": "Tìm kiếm",
            "Settings": "Cài đặt",
            "Upload": "Tải lên",
            "Download": "Tải xuống",
            "Delete": "Xóa",
            "Rename": "Đổi tên",
            "Share": "Chia sẻ",
            "Copy Link": "Sao chép liên kết",
            "Move": "Di chuyển",
            "Favourites": "Yêu thích",
            "Recent": "Gần đây",
            "Teams": "Nhóm",
            "Trash": "Thùng rác",
            "My Drive": "Tài liệu của tôi",
            "Shared": "Được chia sẻ",
            "Users": "Người dùng",
            "Storage": "Lưu trữ",
            "Tags": "Nhãn",
        }

        # Try to load custom translations from CSV and merge
        custom_translations = get_custom_translations()
        if custom_translations:
            translations.update(custom_translations)
            print(f"DEBUG: Updated with {len(custom_translations)} custom translations")

        print(f"DEBUG: Returning {len(translations)} total translations")

        return translations

    except Exception as e:
        frappe.log_error(f"Translation error: {str(e)}")
        print(f"DEBUG: Translation error: {str(e)}")
        # Fallback to basic translations
        return {"Home": "Tài liệu của tôi", "Search": "Tìm kiếm", "Settings": "Cài đặt"}


def get_custom_translations():
    """Load custom translations from CSV file"""
    translations = {}
    try:
        # Get the path to the CSV file
        app_path = frappe.get_app_path("drive")
        csv_path = os.path.join(app_path, "translations", "vi.csv")

        print(f"DEBUG: Looking for translations at: {csv_path}")
        print(f"DEBUG: File exists: {os.path.exists(csv_path)}")

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_reader = csv.DictReader(f)
                print(f"DEBUG: CSV headers: {csv_reader.fieldnames}")

                row_count = 0
                for row in csv_reader:
                    row_count += 1
                    if row_count <= 3:  # Debug first 3 rows
                        print(f"DEBUG: Row {row_count}: {row}")

                    if row.get("Source Text") and row.get("Translated Text"):
                        # Skip comment lines
                        if not row["Source Text"].startswith("#"):
                            source = row["Source Text"].strip()
                            target = row["Translated Text"].strip()
                            translations[source] = target

                print(f"DEBUG: Total rows processed: {row_count}")
                print(f"DEBUG: Loaded {len(translations)} translations")

                # Show some examples
                examples = ["Home", "Search", "Upload", "Settings", "Delete"]
                for example in examples:
                    if example in translations:
                        print(f"DEBUG: {example} -> {translations[example]}")

        else:
            print(f"DEBUG: CSV file not found at: {csv_path}")
            # Try alternative paths
            alt_paths = [
                os.path.join(app_path, "drive", "translations", "vi.csv"),
                "./drive/translations/vi.csv",
                "../drive/translations/vi.csv",
            ]
            for alt_path in alt_paths:
                print(
                    f"DEBUG: Checking alternative path: {alt_path} - exists: {os.path.exists(alt_path)}"
                )

    except Exception as e:
        print(f"DEBUG: Custom translation error: {str(e)}")
        frappe.log_error(f"Custom translation error: {str(e)}")

    return translations
