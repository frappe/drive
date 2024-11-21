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
        field_new_value = self.valid_until
        for child in children:
            child.valid_until = field_new_value
            child.save()
        return

    def validate_general_access(self):
        if self.everyone or self.public:
            self.user_name = None
            self.user_doctype = None
        elif self.user_name or self.user_doctype:
            self.everyone = None
            self.public= None
        if not any([self.everyone, self.public, self.user_name, self.user_doctype]):
            raise ValueError("Invalid Share")


    def after_insert(self):
        doc = self.get_doc()
        owner = get_fullname(self.owner)
        title, entity_document = frappe.db.get_value(
            "Drive Entity", self.share_name, ["title", "document"]
        )
        access_level = 2 if self.write else 1

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
        if self.protected:
            return

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
        if self.everyone:
            doc.add_comment("Shared", _("{0} shared this document with everyone").format(owner))
            message = f"{owner} shared {title} with everyone"
            create_new_activity_log(
                entity=self.share_name,
                document_field="everyone",
                activity_type="share_add",
                activity_message=message,
                field_old_value=False,
                field_new_value=True,
                field_meta_value=access_level,
            )
        elif self.public:
            doc.add_comment("Shared", _("{0} shared this document publicly").format(owner))
            message = f"{owner} shared {title} publicly"
            create_new_activity_log(
                entity=self.share_name,
                document_field="public",
                activity_type="share_add",
                activity_message=message,
                field_old_value=False,
                field_new_value=True,
                field_meta_value=access_level,
            )
        elif self.user_doctype == "User Group":
            message = f"{owner} shared {title} with {self.user_name}"
            create_new_activity_log(
                entity=self.share_name,
                document_field="User Group",
                activity_type="share_add",
                activity_message=message,
                field_old_value=None,
                field_new_value=self.user_name,
                field_meta_value=access_level,
            )
            doc.add_comment(
                "Shared", _("{0} shared this document with {1}").format(owner, (self.user_name))
            )
        else:
            share_username = frappe.db.get_value("User", {"name": self.user_name}, ["full_name"])
            message = f"{owner} shared {title} with {share_username}"
            create_new_activity_log(
                entity=self.share_name,
                document_field="User",
                activity_type="share_add",
                activity_message=message,
                field_old_value=None,
                field_new_value=self.user_name,
                field_meta_value=access_level,
            )

            doc.add_comment(
                "Shared",
                _("{0} shared this document with {1}").format(owner, get_fullname(self.user_name)),
            )

    def on_update(self):
        if self.is_new_record():
            return
        doc = self.get_doc()
        owner = get_fullname(self.owner)
        title = frappe.db.get_value("Drive Entity", self.share_name, ["title"])
        access_level = 2 if self.write else 1
        if self.everyone:
            doc.add_comment("Shared", _("{0} shared this document with everyone").format(owner))
            message = f"{owner} shared {title} with everyone"
            create_new_activity_log(
                entity=self.share_name,
                document_field="everyone",
                activity_type="share_edit",
                activity_message=message,
                field_old_value=False,
                field_new_value=True,
                field_meta_value=access_level,
            )
        elif self.public:
            doc.add_comment("Shared", _("{0} shared this document publicly").format(owner))
            message = f"{owner} shared {title} publicly"
            create_new_activity_log(
                entity=self.share_name,
                document_field="public",
                activity_type="share_edit",
                activity_message=message,
                field_old_value=False,
                field_new_value=True,
                field_meta_value=access_level,
            )
        elif self.user_doctype == "User Group":
            message = f"{owner} shared {title} with {self.user_name}"
            create_new_activity_log(
                entity=self.share_name,
                document_field="User Group",
                activity_type="share_edit",
                activity_message=message,
                field_old_value=None,
                field_new_value=self.user_name,
                field_meta_value=access_level,
            )
            doc.add_comment(
                "Shared", _("{0} shared this document with {1}").format(owner, (self.user_name))
            )
        else:
            share_username = frappe.db.get_value("User", {"name": self.user_name}, ["full_name"])
            message = f"{owner} shared {title} with {share_username}"
            create_new_activity_log(
                entity=self.share_name,
                document_field="User",
                activity_type="share_edit",
                activity_message=message,
                field_old_value=None,
                field_new_value=self.user_name,
                field_meta_value=access_level,
            )

    def is_new_record(self):
        return not self.get_doc_before_save()

    def check_share_permission(self):
        if not self.flags.ignore_share_permission and not frappe.has_permission(
            self.share_doctype, "share", self.get_doc()
        ):
            frappe.throw(_('You need to have "Share" permission'), frappe.PermissionError)

    def on_trash(self):
        if not self.flags.ignore_share_permission:
            self.check_share_permission()
        doc = self.get_doc()
        owner = get_fullname(self.owner)
        title = frappe.db.get_value("Drive Entity", self.share_name, ["title"])
        access_level = 2 if self.write else 1
        if self.everyone:
            doc.add_comment("Shared", _("{0} shared this document with everyone").format(owner))
            message = f"{owner} shared {title} with everyone"
            create_new_activity_log(
                entity=self.share_name,
                document_field="everyone",
                activity_type="share_remove",
                activity_message=message,
                field_old_value=False,
                field_new_value=True,
                field_meta_value=access_level,
            )
        elif self.public:
            doc.add_comment("Shared", _("{0} shared this document publicly").format(owner))
            message = f"{owner} shared {title} publicly"
            create_new_activity_log(
                entity=self.share_name,
                document_field="public",
                activity_type="share_remove",
                activity_message=message,
                field_old_value=False,
                field_new_value=True,
                field_meta_value=access_level,
            )
        elif self.user_doctype == "User Group":
            message = f"{owner} shared {title} with {self.user_name}"
            create_new_activity_log(
                entity=self.share_name,
                document_field="User Group",
                activity_type="share_remove",
                activity_message=message,
                field_old_value=None,
                field_new_value=self.user_name,
                field_meta_value=access_level,
            )
        else:
            share_username = frappe.db.get_value("User", {"name": self.user_name}, ["full_name"])
            message = f"{owner} shared {title} with {share_username}"
            create_new_activity_log(
                entity=self.share_name,
                document_field="User",
                activity_type="share_remove",
                activity_message=message,
                field_old_value=None,
                field_new_value=self.user_name,
                field_meta_value=access_level,
            )

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
