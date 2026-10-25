# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.client import delete, get, set_value

from drive.api.files import set_favourite
from drive.api.notifications import mark_as_read, notify_mentions
from drive.tests.utils import DriveTestCase, make_file, OTHER, OWNER

# A change to try on each record
CHANGES = {
    "Drive Notification": ("read", 1),
    "Drive Settings": ("single_click", 1),
    "Drive Favourite": ("user", OTHER),
    "Drive Entity Log": ("user", OTHER),
}


class TestPersonalRecords(DriveTestCase):
    """Notifications, settings, favourites and recents belong to one person."""

    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "notes.txt", "hello")
        if not frappe.db.exists("Drive Settings", OWNER):
            frappe.get_doc({"doctype": "Drive Settings", "user": OWNER}).insert()
        set_favourite([{"name": self.file.name, "is_favourite": True}])
        self.records = {
            "Drive Notification": frappe.get_doc(
                {"doctype": "Drive Notification", "to_user": OWNER, "type": "Team", "message": "x"}
            )
            .insert(ignore_permissions=True)
            .name,
            "Drive Settings": OWNER,
            "Drive Favourite": frappe.db.get_value("Drive Favourite", {"user": OWNER, "entity": self.file.name}),
            "Drive Entity Log": frappe.get_doc(
                {
                    "doctype": "Drive Entity Log",
                    "user": OWNER,
                    "entity_name": self.file.name,
                    "last_interaction": frappe.utils.now(),
                }
            )
            .insert()
            .name,
        }

    def test_other_people_cannot_read_change_or_delete_them(self):
        frappe.set_user(OTHER)
        for doctype, name in self.records.items():
            with self.subTest(doctype=doctype):
                self.assertNotIn(name, frappe.get_list(doctype, pluck="name", limit_page_length=0))
                with self.assertRaises(frappe.PermissionError):
                    get(doctype, name)
                with self.assertRaises(frappe.PermissionError):
                    set_value(doctype, name, *CHANGES[doctype])
                with self.assertRaises(frappe.PermissionError):
                    delete(doctype, name)
                self.assertTrue(frappe.db.exists(doctype, name))

        for doc in (
            {"doctype": "Drive Settings", "user": OWNER},
            {"doctype": "Drive Notification", "to_user": OWNER, "from_user": OTHER, "type": "Team"},
        ):
            with self.subTest(doctype=doc["doctype"]), self.assertRaises(frappe.PermissionError):
                frappe.get_doc(doc).insert()

    def test_their_person_can_still_use_them(self):
        for doctype, name in self.records.items():
            with self.subTest(doctype=doctype):
                self.assertIn(name, frappe.get_list(doctype, pluck="name", limit_page_length=0))
                self.assertEqual(get(doctype, name)["name"], name)

        set_value("Drive Settings", OWNER, "auto_detect_links", 1)
        set_favourite([{"name": self.file.name, "is_favourite": False}])
        self.assertFalse(frappe.db.exists("Drive Favourite", self.records["Drive Favourite"]))

    def test_only_the_recipient_marks_a_notification_read(self):
        name = self.records["Drive Notification"]
        frappe.set_user(OTHER)
        mark_as_read(name)
        self.assertFalse(frappe.db.get_value("Drive Notification", name, "read"))

        frappe.set_user(OWNER)
        mark_as_read(name)
        self.assertTrue(frappe.db.get_value("Drive Notification", name, "read"))

    def test_drive_still_notifies_other_people(self):
        self.file.share(user=OTHER, read=1)
        notify_mentions(self.file.name, [OTHER])

        mention = frappe.db.get_value("Drive Notification", {"to_user": OTHER, "type": "Mention"})
        self.assertEqual(get("Drive Notification", mention)["from_user"], OWNER)
        with self.assertRaises(frappe.PermissionError):
            set_value("Drive Notification", mention, "message", "Changed")

        frappe.set_user(OTHER)
        mark_as_read(mention)
        self.assertTrue(frappe.db.get_value("Drive Notification", mention, "read"))
