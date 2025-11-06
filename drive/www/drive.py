from __future__ import unicode_literals

import frappe

from drive.api.permissions import get_user_access

no_cache = 1

TITLES = {"login": "Login", "signup": "Create an Account"}


def get_context():
    csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    context = frappe._dict()
    context.boot = get_boot()
    context.boot.csrf_token = csrf_token
    context.csrf_token = csrf_token
    context.site_name = frappe.local.site

    context.title = "Frappe Drive"
    context.description = "Visit Drive online."

    if not frappe.form_dict.app_path:
        return context

    # Parsing
    parts = frappe.form_dict.app_path.split("/")
    if len(parts) >= 3:
        context.description = "Open this online."
        # Ideally add thumbnail, but that might break if there's no thumbnail
        try:
            [title, owner, is_group] = frappe.get_cached_value("Drive File", parts[1], ["title", "owner", "is_group"])
            context.title = "Folder - " + title if is_group else title
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
        }
    )


def get_default_route():
    return "/drive"
