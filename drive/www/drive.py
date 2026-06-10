from __future__ import unicode_literals

import frappe

no_cache = 1

TITLES = {"signup": "Create an Account"}


def get_desk_theme():
    if frappe.session.user == "Guest":
        return "Light"
    return frappe.get_cached_value("User", frappe.session.user, "desk_theme") or "Light"


def get_context():
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    context = frappe._dict()
    context.boot = get_boot()
    context.boot.csrf_token = csrf_token
    context.desk_theme = context.boot.desk_theme
    context.csrf_token = csrf_token
    context.site_name = frappe.local.site

    context.title = "Frappe Drive"
    context.description = "Visit Drive online."

    if not frappe.form_dict.app_path:
        return context

    if frappe.form_dict.app_path == "login" or frappe.form_dict.app_path.startswith("login/"):
        frappe.local.flags.redirect_location = "/login?redirect-to=/drive"
        raise frappe.Redirect

    # Parsing
    parts = frappe.form_dict.app_path.split("/")
    if len(parts) >= 3:
        context.description = "Open this online."
        # Ideally add thumbnail, but that might break if there's no thumbnail
        try:
            [file_name, owner, is_folder] = frappe.get_cached_value(
                "File", parts[1], ["file_name", "owner", "is_folder"]
            )
            context.title = "Folder - " + file_name if is_folder else file_name
            context.description = "Owned by " + frappe.get_cached_value("User", owner, "full_name")
        except:
            pass

    elif parts[0] in TITLES:
        context.title = TITLES[parts[0]]
        context.description = ""
    return context


@frappe.whitelist(methods=["POST"])
def get_context_for_dev():
    if not frappe.conf.developer_mode:
        frappe.throw("This method is only meant for developer mode")
    return get_boot()


def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "default_route": get_default_route(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
            "desk_theme": get_desk_theme(),
        }
    )


def get_default_route():
    return "/drive"
