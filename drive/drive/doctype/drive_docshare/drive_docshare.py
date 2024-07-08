# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_fullname
from drive.api.notifications import notify_share
from drive.api.notifications import notify_mentions

exclude_from_linked_with = True


class DriveDocShare(Document):
    def validate(self):
        self.validate_general_access()
        self.cascade_permissions_downwards()
        self.get_doc().run_method("validate_share", self)

    def get_doc(self):
        if not getattr(self, "_doc", None):
            self._doc = frappe.get_doc(self.share_doctype, self.share_name)
        return self._doc

    def cascade_permissions_downwards(self):
        if self.share or self.write:
            self.read = 1

    def validate_general_access(self):
        if self.everyone | self.public:
            self.user_name = None
            self.user_doctype = None

    def after_insert(self):
        doc = self.get_doc()
        owner = get_fullname(self.owner)
        entity_document = frappe.db.get_value("Drive Entity", self.share_name, ["document"])

        if self.everyone:
            doc.add_comment("Shared", _("{0} shared this document with everyone").format(owner))
        if self.public:
            doc.add_comment("Shared", _("{0} shared this document publicly").format(owner))
        if self.user_doctype == "User Group":
            doc.add_comment(
                "Shared", _("{0} shared this document with {1}").format(owner, (self.user_name))
            )
        else:
            doc.add_comment(
                "Shared",
                _("{0} shared this document with {1}").format(owner, get_fullname(self.user_name)),
            )
        if entity_document:
            frappe.enqueue(
                notify_mentions,
                queue="long",
                job_id=f"fdoc_{entity_document}",
                deduplicate=False,  # Users might've gained access here
                timeout=None,
                now=False,
                at_front=False,
                entity_name=self.share_name,
                document_name=entity_document,
            )

        if self.share_parent is None:
            frappe.enqueue(
                notify_share,
                queue="long",
                job_id=f"fdocshare_{self.name}",
                deduplicate=True,
                timeout=None,
                now=False,
                at_front=False,
                entity_name=self.share_name,
                docshare_name=self.name,
            )

    def check_share_permission(self):
        if not self.flags.ignore_share_permission and not frappe.has_permission(
            self.share_doctype, "share", self.get_doc()
        ):
            frappe.throw(_('You need to have "Share" permission'), frappe.PermissionError)

    def on_trash(self):
        if not self.flags.ignore_share_permission:
            self.check_share_permission()

        self.get_doc().add_comment(
            "Unshared",
            _("{0} un-shared this document with {1}").format(
                get_fullname(self.owner), get_fullname(self.user_name)
            ),
        )


def on_doctype_update():
    """Add index in `tabDocShare` for `(user, document)`"""
    frappe.db.add_index("Drive DocShare", ["user_doctype", "user_name"])
    frappe.db.add_index("Drive DocShare", ["share_doctype", "share_name"])
