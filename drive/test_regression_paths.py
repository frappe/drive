"""
Regression tests for Drive naming / path drift scenarios.

Covers the five scenarios that caused live issues:

  1. naming drift        - stored ``path`` is stale but the file exists at the
                           canonical path (explicit administrator repair; reads never rewrite paths).
  2. duplicate title case - same-titled files at different depths; the removed runtime
                           filename guessing used to crash with
                           ``TypeError: object of type 'PosixPath' has no len()``
                           (regression: same-named copies remain untouched).
  3. missing content files - an active record with no bytes on disk is flagged
                           as MISSING and downloads raise ``frappe.NotFound``.
  4. naming mismatch     - DB ``path`` differs from the canonical path while the
                           file sits at the canonical location -> PATH-FIX.
  5. duplicate folders   - same-titled folders in different branches resolve to
                           DISTINCT canonical paths and never cross-match.

Design:
  - FileManager tests use a temp ``site_folder`` + real Drive File rows (rolled
    back by FrappeTestCase) so nothing on the live site is read or written.
  - repair_paths.run()/verify() classification is tested against a deterministic
    in-memory fake DB + temp site dir (no real files, no real rows).
"""

import shutil
import tempfile
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from drive.drive.doctype.drive_file.drive_file import DriveFile
from drive.utils import repair_paths
from drive.utils.files import FileManager
from drive.utils.repair_paths import find_best_on_disk, same_branch


def _insert_fixture(doc):
    doc.flags.allow_storage_change = True
    return doc.insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Deterministic in-memory DB for repair_paths (mirrors the pymysql cursor API
# that repair_paths._DB expects when ``conn`` is not None).
# ---------------------------------------------------------------------------


class _FakeCursor:
    def __init__(self, db):
        self.db = db
        self._rows = []

    def execute(self, sql, params=None):
        self._rows = self.db.route(sql, params)
        return 0

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class _FakeDB:
    """Routes the exact SQL repair_paths issues against a small folder model."""

    def __init__(self, model):
        self.model = model
        self.executed = []

    def cursor(self):
        return _FakeCursor(self)

    def commit(self):
        pass

    def _home(self):
        for n, m in self.model.items():
            if m["parent"] is None:
                return m
        return None

    def route(self, sql, params=None):
        self.executed.append(sql)
        p = params[0] if params else None

        if "team =" in sql and "parent_entity IS NULL" in sql:  # trash root
            home = self._home()
            return [(home["path"],)] if home else []
        if "parent_entity IS NULL" in sql:  # storage-root probe
            home = self._home()
            return [(home["path"],)] if home else []
        if "SELECT name, path FROM" in sql and "is_group = 0" in sql:  # verify
            return [(n, m["path"]) for n, m in self.model.items() if not m["is_group"]]
        if "AND is_group = 0" in sql:  # active non-group names
            return [(n,) for n, m in self.model.items() if not m["is_group"]]
        if "SELECT title, path, team FROM" in sql:  # run() row
            m = self.model.get(p) or {}
            return [(m["title"], m["path"], m["team"])]
        if "SELECT title, path, parent_entity, is_group FROM" in sql:  # canonical chain
            m = self.model.get(p) or {}
            return [(m["title"], m["path"], m["parent"], int(m["is_group"]))]
        if "SELECT parent_entity FROM" in sql:  # team_of_parent
            m = self.model.get(p) or {}
            return [(m["parent"],)]
        if "SELECT team FROM" in sql:  # team of parent
            m = self.model.get(p) or {}
            return [(m["team"],)]
        return []


def _fake_root(model, site_dir, home_path="rootpath"):
    """Build the private/ root of a fake site whose DB folder model matches."""
    private = site_dir / "private" / "files"
    (private / home_path).mkdir(parents=True, exist_ok=True)
    return private


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPathRegression(FrappeTestCase):
    def setUp(self):
        self.team = frappe.get_doc({"doctype": "Drive Team", "title": "Test Team"}).insert(
            ignore_permissions=True
        )
        self.home = _insert_fixture(frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": "Drive - " + self.team.name,
                "path": "rootpath@example.com",
                "parent_entity": None,
                "is_group": 1,
                "team": self.team.name,
                "is_active": 1,
            }
        ))
        self.disk = Path(tempfile.mkdtemp(prefix="drive-regression-"))
        self._old_site_folder = repair_paths.SITE_FOLDER
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        repair_paths.SITE_FOLDER = self._old_site_folder
        shutil.rmtree(self.disk, ignore_errors=True)

    def _folder(self, title, parent, team=None):
        team = team or self.team.name
        p_path = frappe.db.get_value("Drive File", parent, "path")
        doc = _insert_fixture(frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": title,
                "path": f"{p_path}/{title}",
                "parent_entity": parent,
                "is_group": 1,
                "team": team,
                "is_active": 1,
            }
        ))
        return doc

    def _file(self, title, parent, path=None):
        doc = _insert_fixture(frappe.get_doc(
            {
                "doctype": "Drive File",
                "title": title,
                "path": path,
                "parent_entity": parent,
                "is_group": 0,
                "team": self.team.name,
                "is_active": 1,
            }
        ))
        return doc

    def _manager(self):
        m = FileManager()
        m.site_folder = self.disk
        return m

    # -- 1. naming drift -----------------------------------------------------

    def test_canonical_disk_path_recomputes_from_folder_tree(self):
        folder = self._folder("Folder A", self.home.name)
        fdoc = self._file("drift.txt", folder.name, path="rootpath@example.com/STALE.txt")
        m = self._manager()
        canonical = m._canonical_disk_path(fdoc)
        self.assertEqual(canonical, Path("rootpath@example.com/Folder A/drift.txt"))

    def test_implicit_repair_does_not_bypass_storage_field_validation(self):
        folder = self._folder("Folder A", self.home.name)
        fdoc = self._file("drift.txt", folder.name, path="rootpath@example.com/STALE.txt")
        doc = frappe.get_doc("Drive File", fdoc.name)
        doc.repair_path_drift()
        self.assertEqual(doc.path, "rootpath@example.com/STALE.txt")

    def test_get_file_does_not_rewrite_paths_during_reads(self):
        folder = self._folder("Folder A", self.home.name)
        fdoc = self._file("drift.txt", folder.name, path="rootpath@example.com/STALE.txt")
        canonical = Path("rootpath@example.com/Folder A/drift.txt")
        real = self.disk / canonical
        real.parent.mkdir(parents=True, exist_ok=True)
        real.write_bytes(b"recovered-content")

        with self.assertRaises(frappe.NotFound):
            self._manager().get_file(fdoc)
        self.assertEqual(real.read_bytes(), b"recovered-content")
        self.assertEqual(frappe.db.get_value("Drive File", fdoc.name, "path"), "rootpath@example.com/STALE.txt")

    # -- 2. duplicate title case ---------------------------------------------

    def test_relocate_duplicate_title_different_depths_no_crash(self):
        """Regression for `TypeError: object of type 'PosixPath' has no len()`:
        same-titled copies must remain untouched because their ownership is uncertain."""
        folder = self._folder("Folder A", self.home.name)
        fdoc = self._file("dup.txt", folder.name, path="rootpath@example.com/Folder A/dup.txt")
        canonical = Path("rootpath@example.com/Folder A/dup.txt")

        shallow = self.disk / "rootpath@example.com/dup.txt"  # 2 parts, score 1
        deep = self.disk / "rootpath@example.com/deep/deep/dup.txt"  # 5 parts, score 1
        shallow.parent.mkdir(parents=True, exist_ok=True)
        deep.parent.mkdir(parents=True, exist_ok=True)
        shallow.write_bytes(b"shallow")
        deep.write_bytes(b"deep")

        m = self._manager()
        result = m._relocate_mislocated_file(fdoc, canonical)
        self.assertIsNone(result)
        self.assertFalse((self.disk / canonical).exists())
        self.assertEqual(shallow.read_bytes(), b"shallow")
        self.assertEqual(deep.read_bytes(), b"deep")

    def test_relocate_returns_none_when_no_copy_on_disk(self):
        folder = self._folder("Folder A", self.home.name)
        fdoc = self._file("ghost.txt", folder.name, path="rootpath@example.com/Folder A/ghost.txt")
        canonical = Path("rootpath@example.com/Folder A/ghost.txt")
        m = self._manager()
        self.assertIsNone(m._relocate_mislocated_file(fdoc, canonical))

    def test_same_branch_cross_tree_guard(self):
        canonical = Path("home/TREE-A/sub/x.pdf")
        self.assertTrue(same_branch(canonical, Path("home/TREE-A/sub/x.pdf")))
        self.assertTrue(same_branch(canonical, Path("home/TREE-A/sub/deep/x.pdf")))
        self.assertFalse(same_branch(canonical, Path("home/TREE-B/sub/x.pdf")))
        self.assertFalse(same_branch(canonical, Path("other/x.pdf")))

    def test_find_best_on_disk_never_cross_matches_duplicate_title(self):
        disk_index = {
            Path("home/TREE-A/sub/shared.pdf"): None,
            Path("home/TREE-B/sub/shared.pdf"): None,
        }
        canonical = Path("home/TREE-A/sub/shared.pdf")
        self.assertEqual(find_best_on_disk(disk_index, canonical, "shared.pdf"), Path("home/TREE-A/sub/shared.pdf"))

    # -- 3. missing content files --------------------------------------------

    def test_get_file_raises_not_found_when_no_bytes_on_disk(self):
        folder = self._folder("Folder A", self.home.name)
        fdoc = self._file("ghost.txt", folder.name, path="rootpath@example.com/Folder A/ghost.txt")
        m = self._manager()
        with self.assertRaises(frappe.NotFound):
            m.get_file(fdoc)

    def test_run_flags_missing_content(self):
        site_dir = Path(tempfile.mkdtemp(prefix="drive-site-"))
        self.addCleanup(lambda: shutil.rmtree(site_dir, ignore_errors=True))
        model = {
            "home": {"title": "home", "path": "rootpath", "parent": None, "team": "team1", "is_group": 1},
            "reports": {"title": "Reports", "path": "rootpath/Reports", "parent": "home", "team": "team1", "is_group": 1},
            "f1": {"title": "a.txt", "path": "rootpath/Reports/a.txt", "parent": "reports", "team": "team1", "is_group": 0},
        }
        _fake_root(model, site_dir)
        stats = repair_paths.run(dry_run=True, conn=_FakeDB(model), site_dir=site_dir)
        self.assertEqual(stats["missing"], 1)
        self.assertEqual(stats["errors"], 0)

    def test_verify_counts_missing_file(self):
        site_dir = Path(tempfile.mkdtemp(prefix="drive-site-"))
        self.addCleanup(lambda: shutil.rmtree(site_dir, ignore_errors=True))
        model = {
            "home": {"title": "home", "path": "rootpath", "parent": None, "team": "team1", "is_group": 1},
            "f1": {"title": "a.txt", "path": "rootpath/a.txt", "parent": "home", "team": "team1", "is_group": 0},
        }
        _fake_root(model, site_dir)
        res = repair_paths.verify(conn=_FakeDB(model), site_dir=site_dir)
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["failures"], 1)

    # -- 4. naming mismatch ---------------------------------------------------

    def test_run_path_fix_when_file_is_at_canonical(self):
        site_dir = Path(tempfile.mkdtemp(prefix="drive-site-"))
        self.addCleanup(lambda: shutil.rmtree(site_dir, ignore_errors=True))
        private = _fake_root(None, site_dir)
        (private / "rootpath/Reports").mkdir(parents=True, exist_ok=True)
        (private / "rootpath/Reports/a.txt").write_bytes(b"x")

        model = {
            "home": {"title": "home", "path": "rootpath", "parent": None, "team": "team1", "is_group": 1},
            "reports": {"title": "Reports", "path": "rootpath/Reports", "parent": "home", "team": "team1", "is_group": 1},
            "f1": {"title": "a.txt", "path": "rootpath/Reports/wrong.txt", "parent": "reports", "team": "team1", "is_group": 0},
        }
        stats = repair_paths.run(dry_run=True, conn=_FakeDB(model), site_dir=site_dir)
        self.assertEqual(stats["path_fixed"], 1)
        self.assertEqual(stats["missing"], 0)
        self.assertEqual(stats["errors"], 0)

    # -- 5. duplicate folders -------------------------------------------------

    def test_duplicate_folder_titles_distinct_canonical_paths(self):
        branch_a = self._folder("2024", self.home.name)
        branch_b = self._folder("2025", self.home.name)
        reports_a = self._folder("Reports", branch_a.name)
        reports_b = self._folder("Reports", branch_b.name)
        f_a = self._file("summary.pdf", reports_a.name, path="rootpath@example.com/2024/Reports/summary.pdf")
        f_b = self._file("summary.pdf", reports_b.name, path="rootpath@example.com/2025/Reports/summary.pdf")

        m = self._manager()
        ca = m._canonical_disk_path(f_a)
        cb = m._canonical_disk_path(f_b)
        self.assertEqual(ca, Path("rootpath@example.com/2024/Reports/summary.pdf"))
        self.assertEqual(cb, Path("rootpath@example.com/2025/Reports/summary.pdf"))
        self.assertNotEqual(ca, cb)

    def test_find_best_on_disk_picks_same_branch_for_duplicate_folders(self):
        disk_index = {
            Path("home/2024/Reports/summary.pdf"): None,
            Path("home/2025/Reports/summary.pdf"): None,
        }
        canonical = Path("home/2024/Reports/summary.pdf")
        self.assertEqual(
            find_best_on_disk(disk_index, canonical, "summary.pdf"),
            Path("home/2024/Reports/summary.pdf"),
        )

    # -- repair engine on a multi-branch tree (integration) -------------------

    def test_run_ambiguous_when_only_off_branch_copy_exists(self):
        site_dir = Path(tempfile.mkdtemp(prefix="drive-site-"))
        self.addCleanup(lambda: shutil.rmtree(site_dir, ignore_errors=True))
        private = _fake_root(None, site_dir)
        (private / "rootpath/TREE-B/sub").mkdir(parents=True, exist_ok=True)
        (private / "rootpath/TREE-B/sub/shared.pdf").write_bytes(b"x")

        model = {
            "home": {"title": "home", "path": "rootpath", "parent": None, "team": "team1", "is_group": 1},
            "treeA": {"title": "TREE-A", "path": "rootpath/TREE-A", "parent": "home", "team": "team1", "is_group": 1},
            "subA": {"title": "sub", "path": "rootpath/TREE-A/sub", "parent": "treeA", "team": "team1", "is_group": 1},
            "fA": {"title": "shared.pdf", "path": "rootpath/TREE-A/sub/shared.pdf", "parent": "subA", "team": "team1", "is_group": 0},
        }
        stats = repair_paths.run(dry_run=True, conn=_FakeDB(model), site_dir=site_dir)
        self.assertEqual(stats["ambiguous"], 1)
        self.assertEqual(stats["moved"], 0)
        self.assertEqual(stats["errors"], 0)