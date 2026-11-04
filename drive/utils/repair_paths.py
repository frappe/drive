"""
Legacy Drive path audit and compatibility entry points.

Works on ANY Frappe/Drive site. Two ways to run it:

  1) Via bench (frappe context - uses the site's own DB):

       bench --site YOUR_SITE execute drive.utils.repair_paths.run
       bench --site YOUR_SITE execute drive.utils.repair_paths.run --kwargs "{'dry_run': 1}"
       bench --site YOUR_SITE execute drive.utils.repair_paths.verify

  2) Standalone (no bench, uses pymysql + site_config.json directly):

       python3 -m drive.utils.repair_paths --site YOUR_SITE [--bench-dir ~/frappe-bench] [--apply] [--verify]

It repairs filename/path mismatches between tabDrive File and the files on disk,
using the DB folder tree as the single source of truth:

  1. Computes the canonical path by walking the parent_entity folder chain.
  2. Stored path matches canonical AND file exists on disk -> OK (no change).
  3. File exists at canonical path -> only fix the DB path.
  4. Other file locations -> report for manual recovery.
  5. Unidentified files and trash copies -> leave for manual recovery.
  6. Otherwise -> flag MISSING (no bytes on disk; needs upload).
Team mismatches are reported for manual review, never reassigned automatically.

It NEVER deletes anything. Run with dry_run=True first to review the plan.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import frappe

# ---------------------------------------------------------------------------
# DB abstraction - works in frappe context and standalone (pymysql) mode.
# ---------------------------------------------------------------------------


class _DB:
    """Thin wrapper so callers use fetchone/fetchall/execute the same way in
    frappe context and in standalone pymysql mode."""

    def __init__(self, conn=None):
        self._pymysql = conn
        self._frappe = conn is None

    def fetchone(self, sql, params=None):
        if self._frappe:
            row = frappe.db.sql(sql, params or (), as_dict=False)
            return row[0] if row else None
        cur = self._pymysql.cursor()
        cur.execute(sql, params or ())
        row = cur.fetchone()
        cur.close()
        return row

    def fetchall(self, sql, params=None):
        if self._frappe:
            return frappe.db.sql(sql, params or (), as_dict=False)
        cur = self._pymysql.cursor()
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows

    def execute(self, sql, params=None):
        if self._frappe:
            frappe.db.sql(sql, params or ())
            return
        cur = self._pymysql.cursor()
        cur.execute(sql, params or ())
        cur.close()
        self._pymysql.commit()

    def commit(self):
        if self._frappe:
            frappe.db.commit()
        else:
            self._pymysql.commit()


# ---------------------------------------------------------------------------
# Storage root resolution
# ---------------------------------------------------------------------------


def resolve_storage_root(conn=None, site_dir: Path | None = None):
    """Use private storage only; public legacy files require an explicit migration."""
    global SITE_FOLDER
    SITE_FOLDER = Path(site_dir) / "private" / "files" if site_dir else Path(frappe.get_site_path("private/files"))


def _storage_path(key):
    path = Path(str(key))
    root = SITE_FOLDER.resolve()
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Path leaves Drive storage")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Path leaves Drive storage")
    return resolved


# ---------------------------------------------------------------------------
# Disk index
# ---------------------------------------------------------------------------


def walk_disk() -> dict:
    index = {}
    if not SITE_FOLDER.is_dir():
        return index
    for f in SITE_FOLDER.rglob("*"):
        if f.is_file():
            rel = f.relative_to(SITE_FOLDER)
            try:
                _storage_path(rel)
            except ValueError:
                continue
            if not any(p.startswith(".") for p in rel.parts):
                index[rel] = f
    return index


def canonical_path_for(db, name):
    row = db.fetchone(
        "SELECT title, path, parent_entity, is_group FROM `tabDrive File` WHERE name = %s",
        (name,),
    )
    if not row:
        return None
    title, _, parent, is_group = row

    chain = []
    cur_name = parent
    guard = 0
    while cur_name and guard < 50:
        p = db.fetchone(
            "SELECT title, path, parent_entity, is_group FROM `tabDrive File` WHERE name = %s",
            (cur_name,),
        )
        if not p:
            break
        chain.append(p)
        if not p[3] or not p[2]:  # not a group, or no parent -> root
            break
        cur_name = p[2]
        guard += 1
    if not chain:
        return None

    chain.reverse()
    root_path = (chain[0][1] or "").rstrip("/")
    if not root_path:
        return None
    parts = [r[0] for r in chain[1:]] + [title]
    return str(Path(root_path) / Path(*parts))


def team_of_parent(db, name):
    row = db.fetchone("SELECT parent_entity FROM `tabDrive File` WHERE name = %s", (name,))
    if not row or not row[0]:
        return None
    p = db.fetchone("SELECT team FROM `tabDrive File` WHERE name = %s", (row[0],))
    return p[0] if p else None


def score_path(candidate: Path, chain_titles: set) -> int:
    parts = set(candidate.parts)
    return sum(1 for t in chain_titles if t in parts)


def _normalize(part: str) -> str:
    """Normalize a path component for fuzzy matching (ignores case, spaces,
    hyphens, underscores). 'AMG-ACCOUNTS' and 'AMG_ACCOUNTS' both -> 'amgaccounts'."""
    return re.sub(r"[^a-z0-9]", "", part.lower())


def same_branch(canonical: Path, candidate: Path) -> bool:
    """Require the exact canonical parent chain, preserving case and punctuation."""
    canonical, candidate = Path(canonical), Path(candidate)
    if canonical.is_absolute() or candidate.is_absolute() or ".." in canonical.parts or ".." in candidate.parts:
        return False
    parents = canonical.parts[:-1]
    if not parents:
        return False
    remaining = iter(candidate.parts[:-1])
    return all(part in remaining for part in parents)


def find_best_on_disk(disk_index, canonical: Path, title: str):
    """Find the best same-branch candidate on disk. Never matches cross-tree."""
    canonical = Path(canonical)
    matches = [rel for rel in disk_index if rel.name == title and same_branch(canonical, rel)]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    chain_titles = {_normalize(p) for p in canonical.parts[:-1]}
    scored = sorted(
        matches,
        key=lambda m: (score_path(m, chain_titles), len(m.parts)),
        reverse=True,
    )
    if score_path(scored[0], chain_titles) > score_path(scored[1], chain_titles):
        return scored[0]
    return None


def restore_from_trash(db, team, canonical: Path, dry_run=False) -> bool:
    """A filename cannot identify a trashed record. Leave recovery to an administrator."""
    return False


# ---------------------------------------------------------------------------
# Repair / verify
# ---------------------------------------------------------------------------


def _move_to_canonical(disk_index, db, name, source, canonical_str, stats):
    """Move a single on-disk file to its canonical location and fix the DB row.
    Never raises on a missing source - returns False so the caller can report it."""
    if not same_branch(Path(canonical_str), Path(source)):
        return False
    if db.fetchone("SELECT name FROM `tabDrive File` WHERE path = %s AND name != %s LIMIT 1", (str(source), name)):
        return False
    src = _storage_path(source)
    if not src.is_file():
        return False
    dst = _storage_path(canonical_str)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.move(str(src), str(dst))
    db.execute("UPDATE `tabDrive File` SET path = %s WHERE name = %s", (canonical_str, name))
    db.commit()
    # Remove the consumed source from the disk index so another record can't
    # claim the same file after we moved it.
    disk_index.pop(source, None)
    return True


def run(dry_run=False, conn=None, site_dir=None):
    """Use bounded administrator maintenance in Frappe; standalone access is audit-only.

    Safety rules:
      - DB folder tree is the single source of truth.
      - Applying repairs uses the authenticated, database-only maintenance engine.
      - Standalone audits never move bytes, restore trash or reassign teams.
      - One bad record never aborts the whole run (per-record try/except).
      - Never deletes anything.
    """
    if conn is None:
        from drive.utils.maintenance import inspect_paths

        return inspect_paths(apply=not dry_run)
    if not dry_run:
        raise ValueError("Standalone apply is disabled. Use authenticated site-administrator maintenance.")
    db = _DB(conn)
    resolve_storage_root(conn, site_dir)
    disk_index = walk_disk()

    names = [
        r[0]
        for r in db.fetchall(
            "SELECT name FROM `tabDrive File` WHERE is_active = 1 AND is_group = 0"
        )
    ]

    stats = {
        "ok": 0,
        "path_fixed": 0,
        "moved": 0,
        "restored": 0,
        "team_fixed": 0,
        "ambiguous": 0,
        "missing": 0,
        "errors": 0,
    }
    report = []

    log(f"START | active non-group files: {len(names)} | dry_run={bool(dry_run)} | disk_index={len(disk_index)}")

    for name in names:
        try:
            row = db.fetchone("SELECT title, path, team FROM `tabDrive File` WHERE name = %s", (name,))
            if not row:
                continue
            title, cur_path, team = row

            canonical = canonical_path_for(db, name)

            # 1. Team mismatch (DB tree is source of truth)
            pt = team_of_parent(db, name)
            if pt and pt != team:
                report.append(f"team-fix  {name}  {team} -> {pt}")
                stats["errors"] += 1
                log(f"REFUSED {name}: team does not match its parent")
                continue

            # 2. Path checks
            current = (cur_path or "").rstrip("/")
            if canonical is None:
                report.append(f"missing   {name}  (no canonical path)")
                stats["missing"] += 1
                log(f"MISSING {name}: cannot compute canonical path")
                continue

            canonical = Path(canonical)
            canonical_str = str(canonical).rstrip("/")
            canonical_abs = _storage_path(canonical)
            if db.fetchone("SELECT name FROM `tabDrive File` WHERE path = %s AND name != %s LIMIT 1", (canonical_str, name)):
                stats["ambiguous"] += 1
                continue

            # OK only if DB path AND disk agree. If missing at canonical, fall
            # through to disk search / restore.
            if current == canonical_str and canonical_abs.is_file():
                stats["ok"] += 1
                continue

            if canonical_abs.is_file():
                report.append(f"path-fix  {name}  {current} -> {canonical_str}")
                if not dry_run:
                    db.execute("UPDATE `tabDrive File` SET path = %s WHERE name = %s", (canonical_str, name))
                    db.commit()
                    log(f"FIXED path {name}: {current} -> {canonical_str}")
                stats["path_fixed"] += 1
                continue

            # 3. Move - ONLY from this record's own stored path (safe source) or a
            #    same-branch disk match. Never a cross-tree filename match.
            source = None
            source_label = None
            if current and same_branch(canonical, Path(current)) and _storage_path(current).is_file():
                source = current
                source_label = current
            if source is not None:
                if dry_run:
                    report.append(f"move      {name}  {source_label} -> {canonical_str}")
                    stats["moved"] += 1
                else:
                    if _move_to_canonical(disk_index, db, name, source, canonical_str, stats):
                        report.append(f"move      {name}  {source_label} -> {canonical_str}")
                        log(f"MOVED {name}: {source_label} -> {canonical_str}")
                        stats["moved"] += 1
                    else:
                        # source vanished mid-run (consumed by an earlier record)
                        report.append(f"missing   {name}  {title}  (source vanished)")
                        stats["missing"] += 1
                        log(f"MISSING {name} ({title}): source {source_label} no longer on disk")
                continue

            # 4. Restore from team trash
            if restore_from_trash(db, team, canonical, dry_run=dry_run):
                report.append(f"restore   {name}  (.trash) -> {canonical_str}")
                if not dry_run:
                    db.execute("UPDATE `tabDrive File` SET path = %s WHERE name = %s", (canonical_str, name))
                    db.commit()
                    log(f"RESTORED {name}: .trash -> {canonical_str}")
                stats["restored"] += 1
                continue

            # 5. Any same-named file exists but NOT on this branch? Flag as ambiguous
            #    (never auto-move a possibly-different file across trees).
            elsewhere = [rel for rel in disk_index if rel.name == title and not same_branch(canonical, rel)]
            if elsewhere:
                report.append(f"ambiguous {name}  {title}  (same name off-branch: {elsewhere[0]})")
                stats["ambiguous"] += 1
                log(f"AMBIGUOUS {name} ({title}): off-branch file {elsewhere[0]} not auto-moved")
                continue

            report.append(f"missing   {name}  {title}  (no copy found)")
            stats["missing"] += 1
            log(f"MISSING {name} ({title}): no copy found on disk or trash")
        except Exception as e:
            stats["errors"] += 1
            report.append(f"error     {name}  {e!r}")
            log(f"ERROR {name}: {e!r}")
            continue

    print("=" * 80)
    for line in report:
        print(line)
    print("=" * 80)
    log(
        f"ok={stats['ok']} path_fixed={stats['path_fixed']} moved={stats['moved']} "
        f"restored={stats['restored']} team_fixed={stats['team_fixed']} "
        f"ambiguous={stats['ambiguous']} missing={stats['missing']} errors={stats['errors']} "
        f"| TOTAL: {len(names)}"
    )
    return stats


def verify(conn=None, site_dir=None):
    """Check every active non-group file exists on disk."""
    db = _DB(conn)
    resolve_storage_root(conn, site_dir)

    rows = db.fetchall(
        "SELECT name, path FROM `tabDrive File` WHERE is_active = 1 AND is_group = 0"
    )
    total = len(rows)
    fail = 0
    for name, path in rows:
        try:
            exists = bool(path) and _storage_path(path).is_file()
        except ValueError:
            exists = False
        if not exists:
            fail += 1
            log(f"VERIFY FAIL {name}  path='{path}'  NOT on disk")
    log(f"VERIFY done | total={total} failures={fail}")
    return {"total": total, "failures": fail}


def audit(conn=None, site_dir=None):
    """Read-only report of what the repair WOULD do (no changes)."""
    return run(dry_run=True, conn=conn, site_dir=site_dir)


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

try:
    SITE_FOLDER = Path(frappe.get_site_path("private/files"))
except Exception:
    SITE_FOLDER = None

DEBUG = True


def log(msg):
    line = f"[drive-repair] {msg}"
    print(line)
    if DEBUG:
        try:
            frappe.logger().info(line)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Standalone entry (when run as a script)
# ---------------------------------------------------------------------------


def _standalone_connect(site_dir: Path):
    import json

    import pymysql

    with open(site_dir / "site_config.json") as f:
        conf = json.load(f)
    return pymysql.connect(
        host=conf.get("db_host") or "127.0.0.1",
        port=int(conf.get("db_port") or 3306),
        user=conf.get("db_name"),
        password=conf.get("db_password"),
        database=conf.get("db_name"),
        autocommit=False,
        charset="utf8mb4",
    )


def _main():
    parser = argparse.ArgumentParser(description="Reusable Drive path repair patch")
    parser.add_argument("--site", help="Site name, e.g. astromindev.nvi.frappe.cloud")
    parser.add_argument("--bench-dir", default=None, help="Path to frappe-bench root (auto-detect if omitted)")
    group = parser.add_argument_group("actions")
    group.add_argument("--dry-run", action="store_true", help="Audit only, no changes (default)")
    group.add_argument("--audit", action="store_true", help="Read-only categorized report (no changes)")
    group.add_argument("--apply", action="store_true", help="Apply repairs (moves files + updates DB)")
    group.add_argument("--verify", action="store_true", help="Check every file exists on disk")
    args = parser.parse_args()

    site = args.site
    if not site:
        sys.exit("ERROR: --site is required when running standalone (or run via bench execute)")

    bench_root = Path(args.bench_dir or Path.home() / "frappe-bench")
    site_dir = bench_root / "sites" / site
    if not (site_dir / "site_config.json").is_file():
        sys.exit(f"ERROR: no site_config.json at {site_dir}")

    conn = _standalone_connect(site_dir)
    try:
        if args.verify:
            verify(conn=conn, site_dir=site_dir)
        elif args.audit:
            audit(conn=conn, site_dir=site_dir)
        else:
            run(dry_run=not args.apply, conn=conn, site_dir=site_dir)
    finally:
        conn.close()


if __name__ == "__main__":
    _main()
