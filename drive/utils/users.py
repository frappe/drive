import os

import frappe
import requests
from frappe.rate_limiter import rate_limit
from frappe.utils import now


def mark_as_viewed(entity):
    if (
        frappe.session.user == "Guest"
        or not frappe.has_permission(doctype="Drive Entity Log", ptype="write", user=frappe.session.user)
        or entity.is_group
    ):
        return

    entity_log = frappe.db.get_value("Drive Entity Log", {"entity_name": entity.name, "user": frappe.session.user})
    if entity_log:
        frappe.db.set_value("Drive Entity Log", entity_log, "last_interaction", now(), update_modified=False)
        return
    doc = frappe.new_doc("Drive Entity Log")
    doc.entity_name = entity.name
    doc.user = frappe.session.user
    doc.last_interaction = now()
    doc.insert()
    return doc


@frappe.whitelist()
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

        try:
            res = requests.get(f"https://pro.ip-api.com/json/{ip}?fields={','.join(fields)}")
            data = res.json()
            if data.get("status") != "fail":
                return data
        except Exception:
            pass

        return {}

    return frappe.cache().hget("ip_country_map", ip, generator=_get_country_info)
