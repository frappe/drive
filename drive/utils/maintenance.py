"""Administrator maintenance that never guesses ownership or moves file contents."""

from pathlib import Path

import frappe


def require_site_admin():
    user = frappe.session.user
    if user == "Guest" or (user != "Administrator" and "System Manager" not in frappe.get_roles(user)):
        frappe.throw("Only site administrators can maintain Drive storage.", frappe.PermissionError)


def inspect_paths(apply=False):
    """Audit active paths; optionally repair missing paths from a verified folder tree.

    Repairs only change database paths when the expected file already exists in
    the same team's private folder and no other record claims it. Existing files,
    ambiguous layouts, links, documents, and remote or flat storage are left alone.
    The caller's POST transaction commits changes; this function never commits.
    """
    require_site_admin()
    from drive.utils.files import FileManager

    manager = FileManager()
    if manager.s3_enabled or manager.flat:
        frappe.throw("Path maintenance requires local folder storage.", frappe.ValidationError)

    records = frappe.get_all(
        "Drive File",
        filters={"is_active": 1},
        fields=["name", "title", "path", "parent_entity", "team", "is_group", "is_link", "document", "mime_type"],
    )
    by_name = {r.name: r for r in records}
    roots = {}
    for row in records:
        if row.is_group and not row.parent_entity:
            roots.setdefault(row.team, []).append(row)

    # Shared/overlapping storage roots do not establish a tenant boundary.
    team_roots = {}
    for team, rows in roots.items():
        if team and len(rows) == 1 and rows[0].path:
            try:
                root = _resolve(manager, rows[0].path)
                if root != manager.site_folder.resolve():
                    team_roots[team] = root
            except (frappe.PermissionError, ValueError, OSError):
                pass
    overlapping = {
        team
        for team, root in team_roots.items()
        for other, other_root in team_roots.items()
        if team != other and (root.is_relative_to(other_root) or other_root.is_relative_to(root))
    }
    team_roots = {team: root for team, root in team_roots.items() if team not in overlapping}

    # Include inactive records: their bytes must never be claimed by an active row.
    claimed = {}
    for row in frappe.get_all("Drive File", fields=["name", "path"]):
        if row.path:
            try:
                claimed.setdefault(_resolve(manager, row.path), set()).add(row.name)
            except (frappe.PermissionError, ValueError, OSError):
                pass

    # Two stale records may both expect the same currently unclaimed path.
    # Reserve expected paths before applying anything so neither can claim it.
    for row in records:
        if row.parent_entity and row.team in team_roots and not (row.is_link or row.document):
            try:
                expected = _expected_path(row, by_name, roots[row.team][0])
                target = _resolve(manager, expected, team_roots[row.team])
                claimed.setdefault(target, set()).add(row.name)
            except (frappe.PermissionError, ValueError, OSError):
                pass

    stats = dict.fromkeys(("ok", "repairable", "updated", "missing", "invalid", "skipped"), 0)
    results = []
    for row in records:
        status, expected = "skipped", None
        if row.parent_entity and not (row.is_link or row.document or row.mime_type == "frappe/slides"):
            try:
                root = team_roots.get(row.team)
                if root is None:
                    raise ValueError("No unambiguous team storage root")
                expected = _expected_path(row, by_name, roots[row.team][0])
                target = _resolve(manager, expected, root)
                current = _resolve(manager, row.path, root) if row.path else None
                if claimed.get(target, set()) - {row.name}:
                    raise ValueError("Another record claims this file")
                if current and current.exists():
                    # A mismatch with two existing files needs human review.
                    status = "ok" if current == target else "invalid"
                elif target.exists() and target.is_dir() == bool(row.is_group):
                    status = "repairable"
                    if apply:
                        frappe.db.set_value("Drive File", row.name, "path", expected, update_modified=False)
                        status = "updated"
                else:
                    status = "missing"
            except (frappe.PermissionError, ValueError, OSError):
                status = "invalid"
        stats[status] += 1
        results.append({"name": row.name, "db_path": row.path, "canonical_path": expected, "status": status})
    return {"stats": stats, "results": results}


def _resolve(manager, key, team_root=None):
    path = Path(str(key))
    if path.is_absolute() or ".." in path.parts or not str(key):
        raise ValueError("Invalid storage path")
    resolved = manager.resolve(path)
    if team_root is not None and not resolved.is_relative_to(team_root):
        raise ValueError("Path leaves this team's storage")
    return resolved


def _expected_path(row, by_name, root):
    parts, visited = [], set()
    node = row
    while node.name != root.name:
        if node.name in visited or len(visited) >= 100 or node.team != root.team:
            raise ValueError("Invalid folder tree")
        visited.add(node.name)
        title = node.title
        if not title or title in (".", "..") or any(c in title for c in ("/", "\\", "\0")):
            raise ValueError("Invalid file name")
        parts.append(title)
        node = by_name.get(node.parent_entity)
        if node is None or not node.is_group or node.document or node.is_link:
            raise ValueError("Invalid parent folder")
    return str(Path(root.path).joinpath(*reversed(parts)))
