# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.client import delete, get, set_value

from drive.api.notifications import mark_as_read, notify_mentions
from drive.api.product import get_updates, pop_update
from drive.api.tags import edit_tag
from drive.tests.utils import DriveTestCase, make_file, OTHER, OWNER
from drive.utils import update_clients
from drive.utils.users import mark_as_viewed

# A change to try on each record
CHANGES = {
    "Drive Notification": ("read", 1),
    "Drive Settings": ("single_click", 1),
    "Drive Favourite": ("user", OTHER),
    "Drive Entity Log": ("user", OTHER),
    "Drive Tag": ("title", "Changed"),
    "Drive Desktop Client": ("user", OTHER),
}


class TestPersonalRecords(DriveTestCase):
    """Notifications, settings, favourites, recents, tags and desktop clients belong to one person."""

    def setUp(self):
        super().setUp()
        self.file = make_file(self.team, "notes.txt", "hello")
        frappe.set_user("Administrator")
        self.client = frappe.get_doc(
            {"doctype": "Drive Desktop Client", "user": OWNER, "team": self.team}
        ).insert()
        frappe.set_user(OWNER)
        if not frappe.db.exists("Drive Settings", OWNER):
            frappe.get_doc({"doctype": "Drive Settings", "user": OWNER}).insert()
        self.records = {
            "Drive Notification": frappe.get_doc(
                {"doctype": "Drive Notification", "to_user": OWNER, "type": "Team", "message": "x"}
            )
            .insert(ignore_permissions=True)
            .name,
            "Drive Settings": OWNER,
            "Drive Favourite": frappe.get_doc(
                {"doctype": "Drive Favourite", "user": OWNER, "entity": self.file.name}
            )
            .insert()
            .name,
            "Drive Entity Log": mark_as_viewed(self.file).name,
            "Drive Tag": frappe.get_doc({"doctype": "Drive Tag", "title": "Mine"}).insert().name,
            "Drive Desktop Client": self.client.name,
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
        edit_tag(self.records["Drive Tag"], "Renamed", "blue")
        self.assertEqual(frappe.db.get_value("Drive Tag", self.records["Drive Tag"], "title"), "Renamed")

    def test_only_the_recipient_marks_a_notification_read(self):
        name = self.records["Drive Notification"]
        frappe.set_user(OTHER)
        mark_as_read(name)
        self.assertFalse(frappe.db.get_value("Drive Notification", name, "read"))

        frappe.set_user(OWNER)
        mark_as_read(name)
        self.assertTrue(frappe.db.get_value("Drive Notification", name, "read"))

    def test_changes_by_teammates_still_reach_everyones_desktop_clients(self):
        frappe.set_user(OTHER)
        update_clients(self.file.name, self.team, "edit")
        with self.assertRaises(frappe.PermissionError):
            get_updates(self.client.name)

        frappe.set_user(OWNER)
        updates = get_updates(self.client.name)
        self.assertEqual([(u["type"], u["entity"]) for u in updates], [("edit", self.file.name)])

        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            pop_update(updates[0]["name"])
        frappe.set_user(OWNER)
        pop_update(updates[0]["name"])
        self.assertEqual(get_updates(self.client.name), [])

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
