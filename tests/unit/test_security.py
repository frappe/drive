"""Isolated security regressions; run with python -m unittest discover -s tests/unit.

Frappe's database, roles and whitelist registry are replaced with small fakes.
Storage reads use real temporary files and the actual FileManager class body.
These tests do not replace the Frappe HTTP/database integration suite.
"""

import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile


REPO = Path(__file__).resolve().parents[2]


class Row(dict):
    __setattr__ = dict.__setitem__

    def __getattr__(self, name):
        return self.get(name)


class Denied(Exception):
    pass


class Invalid(Exception):
    pass


class Missing(Exception):
    pass


def load_file(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_definitions(relative, names, namespace):
    tree = ast.parse((REPO / relative).read_text())
    tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    exec(compile(tree, relative, "exec"), namespace)
    return namespace


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.site = Path(self.tmp.name)
        self.root = self.site / "private/files"
        self.root.mkdir(parents=True)
        self.rows = {}
        self.roles = {"admin": ["System Manager"], "member": ["Drive User"], "team-admin": ["Drive Admin"]}
        self.readable = set()
        self.updates = []
        self.frappe = ModuleType("frappe")
        self.frappe.session = SimpleNamespace(user="admin")
        self.frappe.PermissionError = Denied
        self.frappe.ValidationError = Invalid
        self.frappe.NotFound = Missing
        self.frappe.DoesNotExistError = Missing
        self.frappe.throw = lambda message, error=Invalid: self.fail_with(error, message)
        self.frappe.get_roles = lambda user: self.roles.get(user, [])
        self.frappe.get_all = Mock(side_effect=self.get_all)
        self.frappe.get_value = lambda doctype, name, fields, **kwargs: self.rows.get(name)
        self.frappe.get_site_path = lambda *parts: str(self.site.joinpath(*parts))
        self.frappe.db = SimpleNamespace(set_value=Mock(side_effect=self.update), commit=Mock())
        self.frappe.utils = ModuleType("frappe.utils")
        self.frappe.utils.get_site_path = self.frappe.get_site_path
        self.frappe.local = SimpleNamespace(request=SimpleNamespace(environ={}))

        def whitelist(allow_guest=False, methods=None):
            def decorate(function):
                function.allow_guest = allow_guest
                function.allowed_methods = methods
                return function
            return decorate

        self.frappe.whitelist = whitelist
        ns = load_definitions(
            "drive/utils/files.py", {"FileManager"},
            {"frappe": self.frappe, "Path": Path, "DriveFile": object, "BytesIO": io.BytesIO,
             "os": os, "shutil": shutil, "contextmanager": contextlib.contextmanager},
        )
        self.manager = ns["FileManager"].__new__(ns["FileManager"])
        self.manager.site_folder = self.root
        self.manager.s3_enabled = False
        self.manager.flat = False
        self.file_module = ModuleType("drive.utils.files")
        self.file_module.FileManager = lambda: self.manager
        permissions = ModuleType("drive.api.permissions")
        permissions.user_has_permission = lambda name, mode: name in self.readable
        werkzeug_utils = ModuleType("werkzeug.utils")
        werkzeug_utils.send_file = self.send_file
        self.modules = patch.dict(sys.modules, {
            "frappe": self.frappe, "frappe.utils": self.frappe.utils,
            "drive.utils.files": self.file_module, "drive.api.permissions": permissions,
            "werkzeug.utils": werkzeug_utils,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.maintenance = load_file("maintenance_security_test", "drive/utils/maintenance.py")
        sys.modules["drive.utils.maintenance"] = self.maintenance
        self.download = load_file("drive.api.download_security_test", "drive/api/download.py")
        self.api = load_definitions("drive/api/files.py", {"run_drive_audit", "run_drive_repair"}, {"frappe": self.frappe})
        self.add_row("root-a", "A", "team-a", "team-a", is_group=1)
        self.add_row("root-b", "B", "team-b", "team-b", is_group=1)
        (self.root / "team-a").mkdir()
        (self.root / "team-b").mkdir()

    @staticmethod
    def fail_with(error, message):
        raise error(message)

    @staticmethod
    def send_file(source, **kwargs):
        return SimpleNamespace(body=source.read(), headers={}, close=source.close)

    def add_row(self, name, title, path, team="team-a", parent=None, **values):
        self.rows[name] = Row(name=name, title=title, path=path, team=team, parent_entity=parent,
                              is_group=0, is_link=0, document=None, mime_type="text/plain", is_active=1)
        self.rows[name].update(values)
        return self.rows[name]

    def get_all(self, doctype, filters=None, fields=None, **kwargs):
        rows = list(self.rows.values())
        if filters:
            rows = [r for r in rows if all(r.get(key) == value for key, value in filters.items())]
        return [Row({key: row.get(key) for key in fields}) for row in rows] if fields else rows

    def update(self, doctype, name, field, value, **kwargs):
        self.updates.append((name, field, value))
        self.rows[name][field] = value

    def test_maintenance_denies_guest_member_and_drive_admin_before_access(self):
        for user in ("Guest", "member", "team-admin"):
            self.frappe.session.user = user
            for name in ("run_drive_audit", "run_drive_repair"):
                with self.subTest(user=user, endpoint=name), self.assertRaises(Denied):
                    self.api[name]()
        self.frappe.get_all.assert_not_called()
        self.frappe.db.set_value.assert_not_called()

    def test_repair_registration_requires_post_and_authenticated_user(self):
        self.assertEqual(self.api["run_drive_repair"].allowed_methods, ["POST"])
        self.assertFalse(self.api["run_drive_repair"].allow_guest)
        self.assertFalse(self.api["run_drive_audit"].allow_guest)
        self.assertEqual(self.download.download_zip.allowed_methods, ["POST"])

    def test_admin_audit_is_read_only_and_repair_changes_only_verified_database_path(self):
        self.add_row("mine", "note.txt", "team-a/stale.txt", parent="root-a")
        actual = self.root / "team-a/note.txt"
        actual.write_bytes(b"mine")
        report = self.api["run_drive_audit"]()
        self.assertEqual(report["stats"]["repairable"], 1)
        self.assertEqual(self.updates, [])
        self.api["run_drive_repair"]()
        self.assertEqual(self.updates, [("mine", "path", "team-a/note.txt")])
        self.assertEqual(actual.read_bytes(), b"mine")
        self.assertFalse((self.root / "team-a/stale.txt").exists())
        self.frappe.db.commit.assert_not_called()

    def test_administrator_can_audit_without_a_role_lookup(self):
        self.frappe.session.user = "Administrator"
        self.assertIsInstance(self.api["run_drive_audit"](), dict)

    def test_repair_refuses_cross_team_parent_and_storage_path(self):
        for parent, path in (("root-b", "team-a/stale.txt"), ("root-a", "team-b/note.txt")):
            self.add_row("mine", "note.txt", path, parent=parent)
            (self.root / "team-a/note.txt").write_bytes(b"mine")
            (self.root / "team-b/note.txt").write_bytes(b"theirs")
            with self.subTest(parent=parent, path=path):
                self.assertEqual(self.api["run_drive_repair"]()["stats"]["invalid"], 1)
                self.assertEqual(self.updates, [])

    def test_repair_refuses_symlink_and_path_traversal(self):
        outside = self.site / "outside.txt"
        outside.write_bytes(b"private")
        (self.root / "team-a/link.txt").symlink_to(outside)
        for title in ("../outside.txt", "link.txt", "/absolute", "..", "back\\slash"):
            self.add_row("mine", title, "team-a/stale.txt", parent="root-a")
            with self.subTest(title=title):
                self.assertEqual(self.api["run_drive_repair"]()["stats"]["invalid"], 1)
        self.assertEqual(self.updates, [])
        self.assertEqual(outside.read_bytes(), b"private")

    def test_repair_refuses_a_file_claimed_by_another_inactive_record(self):
        self.add_row("mine", "note.txt", "team-a/stale.txt", parent="root-a")
        self.add_row("other", "note.txt", "team-a/note.txt", parent="root-a", is_active=0)
        (self.root / "team-a/note.txt").write_text("other")
        self.assertEqual(self.api["run_drive_repair"]()["stats"]["invalid"], 1)
        self.assertEqual(self.updates, [])

    def test_repair_does_not_guess_from_same_name_in_another_team(self):
        self.add_row("mine", "note.txt", "team-a/stale.txt", parent="root-a")
        other = self.root / "team-b/note.txt"
        other.write_text("theirs")
        self.assertEqual(self.api["run_drive_repair"]()["stats"]["missing"], 1)
        self.assertEqual(self.updates, [])
        self.assertEqual(other.read_text(), "theirs")

    def test_two_stale_records_cannot_claim_the_same_unclaimed_file(self):
        self.add_row("first", "note.txt", "team-a/old-one.txt", parent="root-a")
        self.add_row("second", "note.txt", "team-a/old-two.txt", parent="root-a")
        actual = self.root / "team-a/note.txt"
        actual.write_text("ambiguous")
        self.assertEqual(self.api["run_drive_repair"]()["stats"]["invalid"], 2)
        self.assertEqual(self.updates, [])
        self.assertEqual(actual.read_text(), "ambiguous")

    def test_legacy_console_apply_requires_authenticated_site_administrator(self):
        legacy = load_file("legacy_repair_security_test", "drive/utils/repair_paths.py")
        self.frappe.session.user = "member"
        with self.assertRaises(Denied):
            legacy.run()
        self.frappe.get_all.assert_not_called()
        with self.assertRaises(ValueError):
            legacy.run(conn=object(), dry_run=False, site_dir=self.site)

    def test_legacy_audits_never_restore_trash_by_filename(self):
        legacy = load_file("legacy_repair_security_test", "drive/utils/repair_paths.py")
        legacy.SITE_FOLDER = self.root
        trash = self.root / "team-a/.trash/note.txt"
        trash.parent.mkdir()
        trash.write_bytes(b"unidentified")
        db = SimpleNamespace(fetchall=lambda *args: [("team-a",)])
        for dry_run in (True, False):
            self.assertFalse(legacy.restore_from_trash(db, "team-a", Path("team-a/note.txt"), dry_run=dry_run))
        self.assertEqual(trash.read_bytes(), b"unidentified")
        self.assertFalse((self.root / "team-a/note.txt").exists())

    def test_legacy_storage_boundaries_and_literal_team_names(self):
        legacy = load_file("legacy_repair_security_test", "drive/utils/repair_paths.py")
        legacy.SITE_FOLDER = self.root
        self.assertFalse(legacy.same_branch(Path("TEAM-A/f.txt"), Path("TEAM_A/f.txt")))
        self.assertFalse(legacy.same_branch(Path("Team/f.txt"), Path("team/f.txt")))
        with self.assertRaises(ValueError):
            legacy._storage_path("../../site_config.json")

    def test_repair_refuses_overlapping_team_roots_and_remote_storage(self):
        self.rows["root-b"].path = "team-a/nested"
        self.add_row("mine", "note.txt", "team-a/stale.txt", parent="root-a")
        (self.root / "team-a/note.txt").write_text("mine")
        self.assertEqual(self.api["run_drive_repair"]()["stats"]["invalid"], 1)
        for flag in ("flat", "s3_enabled"):
            setattr(self.manager, flag, True)
            with self.subTest(flag=flag), self.assertRaises(Invalid):
                self.api["run_drive_repair"]()
            setattr(self.manager, flag, False)

    def test_file_reads_refuse_storage_escape_and_do_not_relocate_other_files(self):
        other = self.root / "team-b/note.txt"
        other.write_bytes(b"theirs")
        entity = Row(name="mine", title="note.txt", path="team-a/missing.txt")
        with self.assertRaises(Missing):
            self.manager.get_file(entity)
        self.assertEqual(other.read_bytes(), b"theirs")
        self.assertEqual(self.updates, [])
        for path in ("../../site_config.json", str(self.site / "site_config.json")):
            entity.path = path
            with self.subTest(path=path), self.assertRaises(Denied):
                self.manager.get_file(entity)

    def test_zip_reads_use_the_storage_boundary(self):
        outside = self.site / "outside.txt"
        outside.write_text("secret")
        (self.root / "team-a/link.txt").symlink_to(outside)
        for key in ("../../outside.txt", "team-a/link.txt", str(outside)):
            with self.subTest(key=key), self.assertRaises(Denied):
                with self.download._open_entity_file(self.manager, Row(path=key)):
                    self.fail("Unsafe storage path was opened")

    def test_embed_requires_its_own_read_permission_and_matching_parent(self):
        self.frappe.get_value = lambda doctype, name, *args, **kwargs: None if isinstance(name, dict) else Row(document="writer-doc")
        embed = Row(parent_entity="parent", path="team-a/embed.png", team="team-a")
        self.frappe.get_cached_doc = lambda *args: embed
        readable = {"parent", "embed"}
        namespace = load_definitions(
            "drive/api/embed.py", {"get_file_content"},
            {"frappe": self.frappe, "user_has_permission": lambda name, mode: name in readable,
             "get_file_internal": lambda row: b"allowed"},
        )
        embed.parent_entity = "another-parent"
        with self.assertRaises(Denied):
            namespace["get_file_content"]("embed", "parent")
        embed.parent_entity = "parent"
        readable.remove("embed")
        with self.assertRaises(Denied):
            namespace["get_file_content"]("embed", "parent")
        readable.add("embed")
        self.assertEqual(namespace["get_file_content"]("embed", "parent"), b"allowed")

    def test_zip_checks_each_descendants_access(self):
        self.readable.add("root-a")
        self.add_row("private", "private.txt", "team-a/private.txt", parent="root-a")
        with zipfile.ZipFile(io.BytesIO(), "w") as archive, self.assertRaises(Denied):
            self.download._zip_entity(self.manager, "root-a", archive, Path())

    def test_estimates_require_read_access_before_querying_metadata(self):
        self.frappe.get_value = Mock()
        with self.assertRaises(Denied):
            self.download.estimate_download("team-a", ["private"])
        self.frappe.get_value.assert_not_called()

    def test_zip_rejects_unsafe_archive_names(self):
        self.readable.add("mine")
        for title in ("../x", "/absolute", "..", "back\\slash"):
            self.add_row("mine", title, "team-a/note.txt", parent="root-a")
            with self.subTest(title=title), zipfile.ZipFile(io.BytesIO(), "w") as archive, self.assertRaises(Invalid):
                self.download._zip_entity(self.manager, "mine", archive, Path())

    def test_download_ids_reject_traversal_before_reading_artifacts(self):
        for value in ("../escape", "/absolute", "a" * 31, "a" * 33, None):
            for call in (self.download.download_status, self.download.get_download_zip):
                with self.subTest(value=value, call=call.__name__), self.assertRaises(Invalid):
                    call(value)

    def test_status_and_zip_fail_closed_without_matching_ownership(self):
        download_id = "a" * 32
        status_path = self.download._status_path(download_id)
        status_path.parent.mkdir()
        self.download._zip_path(download_id).write_bytes(b"archive")
        for status in ({"status": "ready"}, {"status": "ready", "user": "other"}, [], "invalid JSON"):
            status_path.write_text(json.dumps(status) if status != "invalid JSON" else status)
            for call in (self.download.download_status, self.download.get_download_zip):
                with self.subTest(status=status, call=call.__name__), self.assertRaises(Denied):
                    call(download_id)
        status_path.unlink()
        with self.assertRaises(Missing):
            self.download.get_download_zip(download_id)

    def test_owner_can_download_completed_zip_and_cleanup_still_works(self):
        download_id = "b" * 32
        status_path = self.download._status_path(download_id)
        status_path.parent.mkdir()
        status_path.write_text(json.dumps({"user": "admin", "status": "ready", "filename": "mine.zip"}))
        zip_path = self.download._zip_path(download_id)
        zip_path.write_bytes(b"archive")
        response = self.download.get_download_zip(download_id)
        self.assertEqual(response.body, b"archive")
        self.assertEqual(response.headers["Content-Length"], "7")
        response.close()
        self.assertFalse(zip_path.exists())

    def test_download_artifact_symlinks_cannot_escape_private_storage(self):
        directory = self.root / ".downloads"
        directory.symlink_to(self.site, target_is_directory=True)
        with self.assertRaises(Denied):
            self.download.download_status("a" * 32)

    def test_download_directory_cannot_alias_a_team_folder(self):
        directory = self.root / ".downloads"
        directory.symlink_to(self.root / "team-b", target_is_directory=True)
        with self.assertRaises(Denied):
            self.download.download_status("a" * 32)

    def test_download_artifact_cannot_alias_another_download(self):
        directory = self.download._download_dir()
        directory.mkdir()
        other = directory / (("b" * 32) + ".zip")
        other.write_text("another user's download")
        (directory / (("a" * 32) + ".zip")).symlink_to(other)
        with self.assertRaises(Denied):
            self.download._zip_path("a" * 32)


if __name__ == "__main__":
    unittest.main()
