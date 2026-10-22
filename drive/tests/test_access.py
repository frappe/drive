# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import base64
import io
import os

import frappe
import pycrdt
from frappe.client import insert, save, set_value
from werkzeug.datastructures import FileStorage

from drive.api.activity import get_entity_activity_log
from drive.api.files import (
    create_document_entity,
    get_entity_type,
    list_entity_comments,
    save_doc,
    upload_embed,
    upload_file,
)
from drive.api.permissions import get_teams
from drive.api.product import edit_team, get_all_users, leave_team, remove_user, set_user_access
from drive.api.wiki_integration import get_yjs_content
from drive.patches import reset_custom_permissions
from drive.tests.utils import DriveTestCase, make_file, make_team, make_user, OTHER, OWNER

THIRD = "drive-third@test.io"


def add_member(team, user, access_level=1):
    doc = frappe.get_doc("Drive Team", team)
    doc.append("users", {"user": user, "access_level": access_level})
    doc.save(ignore_permissions=True)


def visible_teams():
    try:
        return frappe.get_list("Drive Team", pluck="name")
    except frappe.PermissionError:
        return []


def edit_yjs(base, edit):
    """Apply `edit` to the editor fragment of a base64 Yjs document and return the new state."""
    doc = pycrdt.Doc()
    if base:
        doc.apply_update(base64.b64decode(base))
    edit(doc.get("default", type=pycrdt.XmlFragment))
    return base64.b64encode(doc.get_update()).decode()


def attach_upload(content=b"embed"):
    frappe.local.form_dict = frappe._dict()
    frappe.local.request = frappe._dict(files={"file": FileStorage(stream=io.BytesIO(content), filename="e.png")})


class TestAccess(DriveTestCase):
    """Who can reach and change files, documents and teams."""

    def test_save_doc_only_writes_the_files_own_document(self):
        # A document in another team that OWNER cannot edit.
        other_team = make_team(OTHER)
        frappe.set_user(OTHER)
        theirs = create_document_entity(other_team, title="Theirs")
        save_doc(theirs.name, doc_name=theirs.document, content="<p>original</p>")

        frappe.set_user(OWNER)
        mine = create_document_entity(self.team, title="Mine")
        with self.assertRaises(frappe.PermissionError):
            save_doc(mine.name, doc_name=theirs.document, content="<p>changed</p>")
        self.assertEqual(frappe.db.get_value("Drive Document", theirs.document, "raw_content"), "<p>original</p>")

    def test_commenters_can_add_comments_but_not_change_content(self):
        doc = create_document_entity(self.team, title="Notes")
        text = edit_yjs(None, lambda f: f.children.append(pycrdt.XmlElement("paragraph", {}, [pycrdt.XmlText("hello")])))
        save_doc(doc.name, doc_name=doc.document, yjs=text, content="<p>hello</p>")
        frappe.get_doc("Drive File", doc.name).share(OTHER, read=1, comment=1)
        frappe.set_user(OTHER)

        edited = edit_yjs(text, lambda f: f.children[0].children[0].insert(5, " world"))
        for params in ({"yjs": edited}, {"content": "<p>hello world</p>"}, {"yjs": text, "content": "<p>bye</p>"}):
            with self.subTest(params=params), self.assertRaises(frappe.PermissionError):
                save_doc(doc.name, doc_name=doc.document, comment=1, **params)
        stored = frappe.db.get_value("Drive Document", doc.document, ["content", "raw_content"])
        self.assertEqual(stored, (text, "<p>hello</p>"))

        commented = edit_yjs(text, lambda f: f.children[0].children[0].format(0, 5, {"comment": {"commentId": "c1"}}))
        save_doc(doc.name, doc_name=doc.document, yjs=commented, comment=1)
        save_doc(doc.name, doc_name=doc.document, content='<p><span data-comment-id="c1">hello</span></p>', comment=1)
        stored = frappe.db.get_value("Drive Document", doc.document, ["content", "raw_content"])
        self.assertEqual(stored, (commented, '<p><span data-comment-id="c1">hello</span></p>'))

        frappe.set_user(make_user(THIRD))
        with self.assertRaises(frappe.PermissionError):
            save_doc(doc.name, doc_name=doc.document, yjs=commented, comment=1)

    def test_upload_session_ids_stay_inside_the_uploads_folder(self):
        relative_path = "../../drive-upload-session.txt"
        outside = frappe.get_site_path("private", "files", "drive-upload-session.txt")
        frappe.local.form_dict = frappe._dict(
            uuid=relative_path, chunk_index="0", total_chunk_count="1", chunk_byte_offset="0"
        )
        frappe.local.request = frappe._dict(
            files={"file": FileStorage(stream=io.BytesIO(b"content"), filename="a.txt")}
        )
        # Size is never reached in one chunk, so the call returns before finishing; the temp write still happens.
        upload_file(team=self.team, total_file_size="999999")
        self.assertFalse(os.path.exists(outside))

    def test_users_cannot_insert_drive_permission_for_themselves(self):
        private_file = make_file(self.team, "private.txt", "private")
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            insert({"doctype": "Drive Permission", "entity": private_file.name, "user": OTHER, "read": 1})

    def test_only_team_admins_can_change_a_team_through_generic_apis(self):
        make_user(THIRD)
        add_member(self.team, OTHER)
        for user in (OTHER, THIRD):
            frappe.set_user(user)
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                set_value("Drive Team", self.team, "s3_bucket", "other-bucket")
            team = frappe.get_doc("Drive Team", self.team).as_dict()
            team["users"].append({"user": user, "access_level": 2})
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                save(team)
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                insert({"doctype": "Drive Team", "title": "Mine", "s3_bucket": "other-bucket", "prefix": "x"})
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                edit_team(self.team, team_name="Taken")
            with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
                remove_user(self.team, OWNER)

        frappe.set_user("Administrator")
        team = frappe.get_doc("Drive Team", self.team)
        self.assertFalse(team.s3_bucket)
        self.assertEqual({m.user: m.access_level for m in team.users}, {OWNER: 2, OTHER: 1})

    def test_team_admins_and_members_can_still_manage_a_team(self):
        make_user(THIRD)
        add_member(self.team, OTHER)
        add_member(self.team, THIRD)

        edit_team(self.team, team_name="Renamed", icon="star")
        set_user_access(self.team, OTHER, 2)
        remove_user(self.team, THIRD)
        frappe.set_user(OTHER)
        leave_team(self.team)

        frappe.set_user("Administrator")
        team = frappe.get_doc("Drive Team", self.team)
        self.assertEqual((team.title, team.icon), ("Renamed", "star"))
        self.assertEqual({m.user for m in team.users}, {OWNER})

    def test_teams_are_hidden_from_guests_and_outsiders(self):
        add_member(self.team, OTHER)
        outsider = make_user(f"drive-outsider-{frappe.generate_hash(length=6)}@test.io")
        for user in ("Guest", outsider):
            frappe.set_user(user)
            with self.subTest(user=user):
                self.assertEqual(visible_teams(), [])
                self.assertFalse(frappe.has_permission("Drive Team", "read", self.team))
                with self.assertRaises(frappe.PermissionError):
                    get_all_users(team=self.team)
                self.assertEqual(get_all_users(team="all"), [])

        frappe.set_user(OTHER)
        self.assertEqual(set(visible_teams()), set(get_teams()))
        self.assertEqual({u["name"] for u in get_all_users(team=self.team)}, {OWNER, OTHER})

    def test_guests_only_reach_files_that_are_shared_publicly(self):
        doc = create_document_entity(self.team, title="Private")
        frappe.set_user("Guest")
        for call in (get_entity_type, list_entity_comments, upload_embed):
            attach_upload()
            with self.subTest(call=call.__name__), self.assertRaises(frappe.PermissionError):
                call(doc.name)
        attach_upload()
        with self.assertRaises(frappe.PermissionError):
            upload_file(team=self.team, parent=doc.name, embed=1)

        frappe.set_user(OWNER)
        frappe.get_doc("Drive File", doc.name).share(read=1)
        frappe.set_user("Guest")
        self.assertEqual(get_entity_type(doc.name)["type"], "document")
        self.assertEqual(list_entity_comments(doc.name), [])
        attach_upload()
        with self.assertRaises(frappe.PermissionError):
            upload_embed(doc.name)

        frappe.set_user(OWNER)
        attach_upload()
        self.assertIn("embed_name=", upload_embed(doc.name)["file_url"])

    def test_document_content_and_activity_need_read_access(self):
        doc = create_document_entity(self.team, title="Notes")
        frappe.set_user(OTHER)
        with self.assertRaises(frappe.PermissionError):
            get_yjs_content(doc.name)
        with self.assertRaises(frappe.PermissionError):
            get_entity_activity_log(doc.name)

    def test_teams_list_is_always_the_current_users(self):
        frappe.set_user(OTHER)
        self.assertNotIn(self.team, get_teams(details=1))
        self.assertNotIn(self.team, frappe.call(get_teams, user=OWNER, details=1))

    def test_customised_permissions_are_reset(self):
        frappe.set_user("Administrator")
        for doctype in reset_custom_permissions.DOCTYPES:
            frappe.get_doc(doctype="Custom DocPerm", parent=doctype, role="All", read=1, create=1).insert()
            frappe.clear_cache(doctype=doctype)
        frappe.set_user(OTHER)
        self.assertTrue(frappe.has_permission("Drive User Invitation", "create"))

        frappe.set_user("Administrator")
        reset_custom_permissions.execute()
        reset_custom_permissions.execute()
        frappe.set_user(OTHER)
        for doctype in reset_custom_permissions.DOCTYPES:
            with self.subTest(doctype=doctype):
                self.assertFalse(frappe.has_permission(doctype, "create"))
