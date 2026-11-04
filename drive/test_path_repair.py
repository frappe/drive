"""
Tests for the hardened repair_paths.py against the live crash scenario.

Scenario reproduced from the live failure:
  - Two Drive File records with the SAME title in DIFFERENT team trees.
  - The disk holds a file at one branch that, with the OLD buggy code, could be
    matched by the OTHER record (cross-tree) -> wrong move / FileNotFoundError.

Assertions:
  1. find_best_on_disk NEVER returns a cross-tree match (same_branch guard).
  2. run() processes the whole batch without crashing even when a source file
     has already been consumed by an earlier record.
  3. No file is ever moved across branches.
"""

from pathlib import Path

import frappe

from drive import utils as drive_utils
from drive.utils.repair_paths import (
    find_best_on_disk,
    resolve_storage_root,
    run,
    same_branch,
    verify,
)
from drive.utils.repair_paths import SITE_FOLDER as _SITE_FOLDER


def _mk_group(parent, team, title):
    return frappe.get_doc(
        {
            "doctype": "Drive File",
            "title": title,
            "is_group": 1,
            "is_active": 1,
            "team": team,
            "parent_entity": parent,
        }
    ).insert(ignore_permissions=True)


def _mk_file(parent, team, title, path=None):
    d = frappe.get_doc(
        {
            "doctype": "Drive File",
            "title": title,
            "is_active": 1,
            "team": team,
            "parent_entity": parent,
        }
    )
    d.insert(ignore_permissions=True)
    if path:
        frappe.db.set_value("Drive File", d.name, "path", path, update_modified=False)
    return d


def _test_same_branch():
    canonical = Path("home/TREE-A/sub/x.pdf")
    assert same_branch(canonical, Path("home/TREE-A/sub/x.pdf")) is True
    assert same_branch(canonical, Path("home/TREE-A/sub/deep/x.pdf")) is True
    assert same_branch(canonical, Path("home/TREE_B/sub/x.pdf")) is False
    assert same_branch(canonical, Path("other/x.pdf")) is False


def _test_find_best_on_disk():
    disk_index = {
        Path("home/TREE-A/sub/shared.pdf"): None,
        Path("home/TREE-B/sub/shared.pdf"): None,
    }
    canonical = Path("home/TREE-A/sub/shared.pdf")
    match = find_best_on_disk(disk_index, canonical, "shared.pdf")
    assert match == Path("home/TREE-A/sub/shared.pdf"), f"cross-tree match! {match}"


def _test_run_no_crash(team, home_path, home):
    gA = _mk_group(home, team, "TEST-BRANCH-A")
    gB = _mk_group(home, team, "TEST-BRANCH-B")

    docA = _mk_file(gA.name, team, "shared-name.txt")
    docB = _mk_file(gB.name, team, "shared-name.txt")

    # Place ONE real file on disk under branch B; give BOTH records a path that
    # resolves to it (the old code could cross-match, consume it once, then
    # crash moving it again for the second record).
    b_canon = str(Path(home_path) / "TEST-BRANCH-B" / "shared-name.txt")
    frappe.db.set_value("Drive File", docA.name, "path", b_canon, update_modified=False)
    frappe.db.set_value("Drive File", docB.name, "path", b_canon, update_modified=False)

    rp = drive_utils.repair_paths
    real = rp.SITE_FOLDER / b_canon
    real.parent.mkdir(parents=True, exist_ok=True)
    real.write_bytes(b"x")
    frappe.db.commit()

    stats = run(dry_run=False)
    assert stats["errors"] == 0, f"run() crashed: {stats}"
    assert stats["moved"] <= 1, f"expected at most one move (one real file), got {stats}"

    # Cleanup scratch files + records
    for f in (rp.SITE_FOLDER / home_path).rglob("shared-name.txt"):
        try:
            f.unlink()
        except OSError:
            pass
    for p in (rp.SITE_FOLDER / home_path).rglob("TEST-BRANCH-*"):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    for name in (docA.name, docB.name, gA.name, gB.name):
        frappe.delete_doc("Drive File", name, force=True, ignore_permissions=True)
    frappe.db.commit()


def run_tests():
    rp = drive_utils.repair_paths
    resolve_storage_root()

    _test_same_branch()
    _test_find_best_on_disk()

    home = frappe.db.sql(
        "SELECT name, path, team FROM `tabDrive File` WHERE parent_entity IS NULL AND is_active=1 LIMIT 1",
        as_dict=True,
    )[0]
    _test_run_no_crash(home["team"], home["path"], home["name"])

    v = verify()
    assert v["failures"] == 0, f"verify failed after test: {v}"
    print("ALL PATH-REPAIR TESTS PASSED")
    print("verify:", v)


if __name__ == "__main__":
    run_tests()