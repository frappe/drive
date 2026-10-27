# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import io
import shutil

import frappe
from werkzeug.datastructures import FileStorage
from werkzeug.test import EnvironBuilder

from drive.api.files import create_folder, get_file_content, get_upload_path, move, stream_file_content, upload_file
from drive.patches import repair_moved_file_paths
from drive.tests.test_controller_method import call
from drive.tests.utils import OTHER, OWNER, DriveTestCase, make_file, read_file
from drive.utils.files import FileManager


class TestMissingFolders(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.manager = FileManager()

    def test_create_folder_when_parent_is_missing_on_disk(self):
        parent = create_folder(self.team, "Parent")
        shutil.rmtree(self.manager.site_folder / parent.path)

        child = create_folder(self.team, "Child", parent=parent.name)
        self.assertTrue((self.manager.site_folder / child.path).is_dir())

    def test_upload_path_when_team_folder_is_missing_on_disk(self):
        path = get_upload_path(f"missing-{frappe.generate_hash(length=8)}/nested", "file.txt")
        self.assertTrue(path.parent.is_dir())

    def test_embed_upload_when_embeds_folder_is_missing(self):
        source = self.manager.site_folder / f"embed-{frappe.generate_hash(length=8)}.png"
        source.write_text("image")
        destination = f"doc-{frappe.generate_hash(length=8)}/.embeds/image.png"

        self.manager.upload_file(
            source, frappe._dict(path=destination, team=self.team, mime_type="image/png"), create_thumbnail=False
        )
        self.assertEqual((self.manager.site_folder / destination).read_text(), "image")

    def test_streaming_a_missing_video_is_not_found(self):
        video = make_file(self.team, "clip.mp4", "video")
        (self.manager.site_folder / video.path).unlink()
        frappe.local.request = frappe._dict(headers={"Range": "bytes=0-"})
        with self.assertRaises(frappe.NotFound):
            stream_file_content(video.name)


class TestFoldersWithOtherMembersFiles(DriveTestCase):
    """OWNER's folder holds a file that OTHER, a team member, uploaded."""

    def setUp(self):
        super().setUp()
        team = frappe.get_doc("Drive Team", self.team)
        team.append("users", {"user": OTHER, "access_level": 1})
        team.save(ignore_permissions=True)
        self.folder = create_folder(self.team, "Shared")

        frappe.set_user(OTHER)
        frappe.local.request = frappe._dict(
            files={"file": FileStorage(stream=io.BytesIO(b"member's file"), filename="notes.txt")}
        )
        self.file = upload_file(team=self.team, parent=self.folder.name, total_file_size="13")
        frappe.local.request = frappe._dict(environ=EnvironBuilder().get_environ())
        self.addCleanup(lambda: setattr(frappe.local, "request", None))
        frappe.set_user(OWNER)

    def assert_member_can_open_their_file(self):
        frappe.set_user(OTHER)
        self.assertEqual(read_file(self.file.name), "member's file")
        self.assertEqual(get_file_content(self.file.name).status_code, 200)

    def test_renaming_or_moving_the_folder_keeps_the_file(self):
        call(self.folder.name, "rename", new_title="Renamed")
        self.assert_member_can_open_their_file()

        frappe.set_user(OWNER)
        outer = create_folder(self.team, "Outer")
        move([self.folder.name], outer.name)
        self.assert_member_can_open_their_file()

    def test_repair_patch_fixes_a_path_left_behind_by_a_folder_rename(self):
        old_path = self.file.path
        call(self.folder.name, "rename", new_title="Renamed")
        new_path = frappe.db.get_value("Drive File", self.file.name, "path")
        # What a rename did before this fix
        frappe.db.set_value("Drive File", self.file.name, "path", old_path)

        repair_moved_file_paths.execute()
        self.assertEqual(frappe.db.get_value("Drive File", self.file.name, "path"), new_path)
        self.assert_member_can_open_their_file()
