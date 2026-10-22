# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import shutil

import frappe

from drive.api.files import create_folder, get_upload_path, stream_file_content
from drive.tests.utils import DriveTestCase, make_file
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
