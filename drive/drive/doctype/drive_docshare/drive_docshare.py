# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_fullname
from drive.api.notifications import notify_share
from drive.api.notifications import notify_mentions
from drive.api.activity import create_new_activity_log

exclude_from_linked_with = True


class DriveDocShare(Document):
    def validate(self):
        self.validate_general_access()
        self.cascade_permissions_downwards()
        self.get_doc().run_method("validate_share", self)
        self.update_children()

    def get_doc(self):
        if not getattr(self, "_doc", None):
            self._doc = frappe.get_doc(self.share_doctype, self.share_name)
        return self._doc

    def cascade_permissions_downwards(self):
        if self.share or self.write:
            self.read = 1

    def update_children(self):
        children = self.get_children()
        new_value = self.valid_until
        for child in children:
            child.valid_until = new_value
            child.save()
        return

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

        entity_document = frappe.db.get_value("Drive Entity", self.share_name, ["title"])
        full_name = frappe.db.get_value("User", {"name": frappe.session.user}, ["full_name"])
        share_username = self.user_name
        if self.user_doctype == "User":
            share_username = frappe.db.get_value("User", {"name": share_username}, ["full_name"])
        message = f"{full_name} shared {entity_document} with {share_username}"
        create_new_activity_log(
            doctype=self.doctype,
            document_name=self.name,
            activity_type="create",
            activity_message=message,
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

    def get_children(self):
        """Return a generator that yields child Documents."""
        child_names = frappe.get_list(
            self.doctype, filters={"share_parent": self.name}, pluck="name"
        )
        for name in child_names:
            yield frappe.get_doc(self.doctype, name)


def on_doctype_update():
    """Add index in `tabDocShare` for `(user, document)`"""
    frappe.db.add_index("Drive DocShare", ["user_doctype", "user_name"])
    frappe.db.add_index("Drive DocShare", ["share_doctype", "share_name"])
