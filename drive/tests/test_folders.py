# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import io
import shutil

import frappe
from botocore.exceptions import ClientError
from werkzeug.datastructures import FileStorage
from werkzeug.test import EnvironBuilder

from drive.api.files import (
    create_folder,
    delete_entities,
    get_file_content,
    get_upload_path,
    move,
    remove_or_restore,
    stream_file_content,
    upload_file,
)
from drive.patches import repair_moved_file_paths
from drive.tests.test_controller_method import call
from drive.tests.utils import OTHER, OWNER, DriveTestCase, make_file, make_team, read_file
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

    def test_restoring_the_folder_under_a_new_name_keeps_the_file(self):
        remove_or_restore([self.folder.name])
        create_folder(self.team, "Shared")
        remove_or_restore([self.folder.name])
        self.assertEqual(frappe.db.get_value("Drive File", self.folder.name, "title"), "Shared (1)")
        self.assert_member_can_open_their_file()

    def test_moving_the_folder_to_another_team_takes_the_file_along(self):
        other_team = make_team(OWNER)
        move([self.folder.name], team=other_team)
        self.assertEqual(frappe.db.get_value("Drive File", self.file.name, "team"), other_team)
        self.assertEqual(read_file(self.file.name), "member's file")

    def test_deleting_the_folder_deletes_the_file(self):
        remove_or_restore([self.folder.name])
        delete_entities([self.folder.name])
        self.assertEqual(frappe.db.get_value("Drive File", self.file.name, "is_active"), -1)

        frappe.get_doc("Drive File", self.folder.name).delete(ignore_permissions=True)
        self.assertFalse(frappe.db.exists("Drive File", self.file.name))

    def test_repair_patch_fixes_a_path_left_behind_by_a_folder_rename(self):
        old_path = self.file.path
        call(self.folder.name, "rename", new_title="Renamed")
        new_path = frappe.db.get_value("Drive File", self.file.name, "path")
        # What a rename did before this fix
        frappe.db.set_value("Drive File", self.file.name, "path", old_path)

        repair_moved_file_paths.execute()
        self.assertEqual(frappe.db.get_value("Drive File", self.file.name, "path"), new_path)
        self.assert_member_can_open_their_file()


class FakeS3:
    """Just enough of an S3 client to move objects."""

    def __init__(self, keys):
        self.objects = dict.fromkeys(keys, b"")

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")

    def copy_object(self, Bucket, CopySource, Key):
        self.objects[Key] = self.objects[CopySource["Key"]]

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)

    def get_paginator(self, operation):
        keys = list(self.objects)
        return frappe._dict(
            paginate=lambda Bucket, Prefix: [{"Contents": [{"Key": key} for key in keys if key.startswith(Prefix)]}]
        )


class TestS3Folders(DriveTestCase):
    def test_moving_a_folder_moves_everything_in_it(self):
        manager = FileManager()
        manager.s3_enabled = True
        manager.conn = FakeS3(["team/Shared/", "team/Shared/notes.txt", "team/Shared/Inner/a.txt", "team/Shared.txt"])

        manager.move(frappe._dict(team=self.team, path="team/Shared/", is_group=1), "team/Renamed")
        self.assertEqual(
            sorted(manager.conn.objects),
            ["team/Renamed/", "team/Renamed/Inner/a.txt", "team/Renamed/notes.txt", "team/Shared.txt"],
        )
