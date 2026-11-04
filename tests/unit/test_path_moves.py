"""Exercise actual rename/storage code with temporary files and fake Frappe records."""

from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import test_security as security
from test_security import Denied, Invalid, Row, load_definitions, load_file


class ClientError(Exception):
    pass


class Document(Row):
    def __getattr__(self, key):
        if key not in self:
            raise AttributeError(key)
        return self[key]


class FakeS3:
    def __init__(self, objects):
        self.objects = dict(objects)

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError(Key)

    def copy_object(self, Bucket, CopySource, Key):
        self.objects[Key] = self.objects[CopySource["Key"]]

    def delete_object(self, Bucket, Key):
        self.objects.pop(Key, None)

    def get_paginator(self, operation):
        return SimpleNamespace(paginate=lambda Bucket, Prefix: [
            {"Contents": [{"Key": key} for key in self.objects if key.startswith(Prefix)]}
        ])


class RenameTests(unittest.TestCase):
    def setUp(self):
        self.fixture = security.SecurityTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.frappe = self.fixture.frappe
        self.rows = self.fixture.rows
        self.manager = self.fixture.manager
        self.saves, self.rollback_callbacks = [], []
        self.authorized = True
        self.frappe.get_all = Mock(side_effect=self.get_all)
        self.frappe.get_doc = lambda doctype, name: self.rows[name]
        self.frappe.get_value = self.get_value
        self.frappe.db.get_value = self.get_value
        self.frappe.db.after_rollback = SimpleNamespace(add=self.rollback_callbacks.append)
        self.manager.bucket_map = {"team-a": "bucket", "team-b": "other-bucket"}
        self.manager.bucket = "bucket"
        # The actual storage method imports ClientError even for a disk move.
        exceptions = ModuleType("botocore.exceptions")
        exceptions.ClientError = ClientError
        self.botocore = patch.dict("sys.modules", {"botocore.exceptions": exceptions})
        self.botocore.start()
        self.addCleanup(self.botocore.stop)
        self.path_moves = load_file("path_moves_test", "drive/utils/path_moves.py")
        self.module = patch.dict("sys.modules", {"drive.utils.path_moves": self.path_moves})
        self.module.start()
        self.addCleanup(self.module.stop)
        self.manager.__class__.get_disk_path.__globals__["get_home_folder"] = self.home
        self.activity = Mock()
        namespace = load_definitions("drive/drive/doctype/drive_file/drive_file.py", {"DriveFile"}, {
            "Document": Document, "frappe": self.frappe, "Path": Path,
            "FileManager": lambda: self.manager, "user_has_permission": lambda *args: self.authorized,
            "get_unused_title": lambda title, *args: title, "get_home_folder": self.home,
            "create_new_activity_log": self.activity, "now": lambda: "now", "update_clients": lambda *args: None,
        })
        self.Doc = namespace["DriveFile"]
        self.Doc.save = lambda doc: self.saves.append(doc.name)
        self.Doc.is_new = lambda doc: False
        self.Doc.has_value_changed = lambda doc, field: True
        self.folder = self.add_doc("folder", "Old", "team-a/Old", "root-a", is_group=1)
        self.disk("team-a/Old").mkdir()

    def home(self, team):
        return self.rows["root-a" if team == "team-a" else "root-b"]

    def get_value(self, doctype, name, field, **kwargs):
        if doctype == "User":
            return "Owner"
        row = self.rows.get(name)
        if row is None:
            return None
        return Row({f: row.get(f) for f in field}) if isinstance(field, list) else row.get(field)

    def get_all(self, doctype, filters=None, fields=None, pluck=None, **kwargs):
        rows = list(self.rows.values())
        for key, value in (filters or {}).items():
            if value == ["is", "not set"]:
                rows = [row for row in rows if not row.get(key)]
            else:
                rows = [row for row in rows if row.get(key) == value]
        if pluck:
            return [row.get(pluck) for row in rows]
        return [Row({field: row.get(field) for field in fields}) for row in rows] if fields else rows

    def add_doc(self, name, title, path, parent, team="team-a", **values):
        doc = self.Doc(name=name, title=title, path=path, parent_entity=parent, team=team,
                       is_group=0, document=None, is_link=0, mime_type="text/plain", owner="owner",
                       doctype="Drive File", flags=Row())
        doc.update(values)
        self.rows[name] = doc
        return doc

    def disk(self, key):
        return self.fixture.root / key

    def write(self, key, data=b"contents"):
        path = self.disk(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def assert_rejected_without_move(self, error=Invalid):
        with self.assertRaises(error):
            self.folder.rename("New")
        self.assertTrue(self.disk("team-a/Old").is_dir())
        self.assertFalse(self.disk("team-a/New").exists())
        self.assertEqual(self.folder.title, "Old")
        self.assertEqual(self.saves, [])
        self.assertEqual(self.rollback_callbacks, [])
        self.activity.assert_not_called()

    def test_stale_child_outside_parent_is_repaired_from_exact_tree_location(self):
        child = self.add_doc("child", "report.txt", "team-a/UNRELATED/report.txt", "folder")
        self.write("team-a/Old/report.txt", b"the correct file")
        self.folder.rename("New")
        self.assertEqual(child.path, "team-a/New/report.txt")
        self.assertEqual(self.disk(child.path).read_bytes(), b"the correct file")
        self.assertFalse(self.disk("team-a/Old").exists())
        self.assertTrue(child.flags.allow_storage_change)

    def test_normal_relative_paths_and_other_members_files_are_preserved(self):
        child = self.add_doc("child", "report.txt", "team-a/Old/report.txt", "folder", owner="member")
        self.write(child.path, b"member's bytes")
        self.folder.rename("New")
        self.assertEqual(child.path, "team-a/New/report.txt")
        self.assertEqual(self.disk(child.path).read_bytes(), b"member's bytes")
        self.assertTrue(child.flags.ignore_permissions)

    def test_nested_stale_folders_are_repaired_before_descendants(self):
        sub = self.add_doc("sub", "Sub", "team-a/WRONG/Sub", "folder", is_group=1)
        child = self.add_doc("child", "report.txt", "team-a/Old/Sub/report.txt", "sub")
        self.write("team-a/Old/Sub/report.txt")
        self.folder.rename("New")
        self.assertEqual(sub.path, "team-a/New/Sub")
        self.assertEqual(child.path, "team-a/New/Sub/report.txt")
        self.assertTrue(self.disk(child.path).is_file())

    def test_valid_embedded_suffix_is_not_flattened(self):
        self.folder.document = "writer-doc"
        child = self.add_doc("embed", "image.png", "team-a/Old/.embeds/image.png", "folder")
        self.write(child.path, b"image")
        self.folder.rename("New")
        self.assertEqual(child.path, "team-a/New/.embeds/image.png")
        self.assertEqual(self.disk(child.path).read_bytes(), b"image")

    def test_stale_embed_uses_the_exact_embeds_directory(self):
        self.folder.document = "writer-doc"
        child = self.add_doc("embed", "image.png", "team-a/stale/image.png", "folder")
        self.write("team-a/Old/.embeds/image.png", b"image")
        self.folder.rename("New")
        self.assertEqual(child.path, "team-a/New/.embeds/image.png")
        self.assertEqual(self.disk(child.path).read_bytes(), b"image")

    def test_existing_stale_location_is_ambiguous_and_rejected_before_move(self):
        self.add_doc("child", "report.txt", "team-a/UNRELATED/report.txt", "folder")
        other = self.write("team-a/UNRELATED/report.txt", b"uncertain")
        self.write("team-a/Old/report.txt", b"also exists")
        self.assert_rejected_without_move()
        self.assertEqual(other.read_bytes(), b"uncertain")

    def test_no_global_filename_search_when_exact_location_is_missing(self):
        self.add_doc("child", "report.txt", "team-a/UNRELATED/report.txt", "folder")
        other = self.write("team-b/report.txt", b"theirs")
        self.assert_rejected_without_move()
        self.assertEqual(other.read_bytes(), b"theirs")

    def test_another_record_claiming_the_expected_file_is_rejected(self):
        self.add_doc("child", "report.txt", "team-a/stale/report.txt", "folder")
        self.add_doc("other", "other.txt", "team-a/Old/report.txt", "root-a", is_active=0)
        self.write("team-a/Old/report.txt")
        self.assert_rejected_without_move()

    def test_two_stale_records_cannot_claim_one_expected_file(self):
        self.add_doc("first", "report.txt", "team-a/one/report.txt", "folder")
        self.add_doc("second", "report.txt", "team-a/two/report.txt", "folder")
        self.write("team-a/Old/report.txt")
        self.assert_rejected_without_move()

    def test_cross_team_child_metadata_and_paths_are_rejected(self):
        child = self.add_doc("child", "report.txt", "team-a/Old/report.txt", "folder", team="team-b")
        self.write(child.path)
        self.assert_rejected_without_move(Denied)
        child.team = "team-a"
        child.path = "team-b/missing.txt"
        self.assert_rejected_without_move(Denied)

    def test_symlink_source_cannot_escape_the_renamed_folder(self):
        self.add_doc("child", "report.txt", "team-a/stale/report.txt", "folder")
        outside = self.write("team-b/report.txt", b"theirs")
        self.disk("team-a/Old/report.txt").symlink_to(outside)
        self.assert_rejected_without_move(Denied)
        self.assertEqual(outside.read_bytes(), b"theirs")

    def test_even_an_in_folder_symlink_is_not_used_as_recovery_evidence(self):
        self.add_doc("child", "report.txt", "team-a/stale/report.txt", "folder")
        original = self.write("team-a/Old/original.txt", b"uncertain")
        self.disk("team-a/Old/report.txt").symlink_to(original)
        self.assert_rejected_without_move()
        self.assertEqual(original.read_bytes(), b"uncertain")

    def test_invalid_stored_keys_cannot_trigger_recovery(self):
        child = self.add_doc("child", "report.txt", "../outside.txt", "folder")
        self.write("team-a/Old/report.txt")
        self.assert_rejected_without_move()
        child.path = str(self.disk("team-a/Old/report.txt"))
        self.assert_rejected_without_move()

    def test_invalid_child_name_fails_before_storage_move(self):
        self.add_doc("child", "../outside", "team-a/stale/report.txt", "folder")
        self.assert_rejected_without_move()

    def test_cycles_fail_before_storage_move(self):
        self.add_doc("child", "report.txt", "team-a/Old/report.txt", "folder")
        self.folder.parent_entity = "child"
        self.assert_rejected_without_move()

    def test_invalid_new_title_is_rejected_before_moving_bytes(self):
        for title in ("../elsewhere", "nested/name", "..", "bad\0name"):
            with self.subTest(title=title), self.assertRaises(Invalid):
                self.folder.rename(title)
            self.assertEqual(self.folder.title, "Old")
            self.assertTrue(self.disk("team-a/Old").is_dir())
        self.assertEqual(self.saves, [])
        self.assertEqual(self.rollback_callbacks, [])

    def test_legacy_path_alias_claiming_the_expected_bytes_is_rejected(self):
        self.add_doc("child", "report.txt", "team-a/stale/report.txt", "folder")
        self.add_doc("other", "old.txt", "team-a/Old/../Old/report.txt", "root-a")
        self.write("team-a/Old/report.txt")
        self.assert_rejected_without_move()

    def test_overlapping_team_root_is_rejected(self):
        self.rows["root-b"].path = "team-a"
        self.assert_rejected_without_move(Denied)

    def test_storage_rollback_callback_is_retained_if_a_save_fails(self):
        child = self.add_doc("child", "report.txt", "team-a/Old/report.txt", "folder")
        self.write(child.path, b"original")
        self.Doc.save = lambda doc: self.fail_save()
        with self.assertRaises(RuntimeError):
            self.folder.rename("New")
        self.assertEqual(len(self.rollback_callbacks), 1)
        self.rollback_callbacks[0]()
        self.assertEqual(self.disk("team-a/Old/report.txt").read_bytes(), b"original")
        self.assertFalse(self.disk("team-a/New").exists())

    @staticmethod
    def fail_save():
        raise RuntimeError("simulated save failure")

    def test_unauthorized_rename_does_not_inspect_or_move_storage(self):
        self.authorized = False
        self.frappe.get_all.reset_mock()
        self.assert_rejected_without_move(Denied)
        self.frappe.get_all.assert_not_called()

    def test_normal_s3_rename_moves_all_objects_and_keeps_subpaths(self):
        child = self.add_doc("child", "report.txt", "team-a/Old/report.txt", "folder", owner="member")
        self.manager.s3_enabled = True
        self.manager.conn = FakeS3({"team-a/Old/": b"", child.path: b"member", "team-a/Old/.embeds/e.png": b"image"})
        embed = self.add_doc("embed", "e.png", "team-a/Old/.embeds/e.png", "folder")
        self.folder.rename("New")
        self.assertEqual(self.manager.conn.objects, {
            "team-a/New/": b"", "team-a/New/report.txt": b"member", "team-a/New/.embeds/e.png": b"image",
        })
        self.assertEqual(embed.path, "team-a/New/.embeds/e.png")

    def test_stale_s3_path_is_rejected_without_object_guessing(self):
        self.add_doc("child", "report.txt", "team-a/stale/report.txt", "folder")
        self.manager.s3_enabled = True
        self.manager.conn = FakeS3({"team-a/Old/": b"", "team-a/Old/report.txt": b"original"})
        original = self.manager.conn.objects.copy()
        self.assert_rejected_without_move()
        self.assertEqual(self.manager.conn.objects, original)

    def test_flat_storage_keeps_the_existing_rename_behavior(self):
        self.manager.flat = True
        original = self.folder.path
        self.folder.rename("New")
        self.assertEqual(self.folder.path, original)
        self.assertEqual(self.folder.title, "New")
        self.assertTrue(self.disk(original).is_dir())

    def test_home_folder_rename_preserves_descendant_paths(self):
        home = self.add_doc("root-a", "A", "team-a", None, is_group=1)
        home.rename("NewRoot")
        self.assertEqual(home.path, "NewRoot")
        self.assertEqual(self.folder.path, "NewRoot/Old")
        self.assertTrue(self.disk("NewRoot/Old").is_dir())
        self.assertTrue(self.disk("team-b").is_dir())

    def test_links_and_slides_do_not_trigger_storage_recovery(self):
        self.folder.is_link = 1
        self.folder.path = "https://example.com"
        self.frappe.get_all.reset_mock()
        self.folder.rename("New")
        self.assertEqual(self.folder.path, "https://example.com")
        self.frappe.get_all.assert_not_called()


if __name__ == "__main__":
    unittest.main()
