from __future__ import unicode_literals
import frappe
from drive.api.permissions import get_user_access

no_cache = 1

TITLES = {"login": "Login", "signup": "Create an Account", "setup": "Set up your Account"}


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
    context.og_image = "https://raw.githubusercontent.com/frappe/drive/main/.github/og_1200.png"

    if not frappe.form_dict.app_path:
        return context

    # Parsing
    parts = frappe.form_dict.app_path.split("/")
    if len(parts) >= 4:
        context.description = "Open this online."
        context.og_image = ""
        doc = frappe.get_doc("Drive File", parts[3])
        if get_user_access(doc)["read"]:
            context.title = "Folder - " + doc.title if doc.is_group else doc.title
            context.description = "Owned by " + doc.owner

            context.og_image = (
                "/api/method/drive.api.thumbnail_generator.create_image_thumbnail?entity_name="
                + doc.name
            )
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
