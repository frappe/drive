"""Plan folder renames before moving bytes, without searching for filename matches."""

from pathlib import Path

import frappe


def plan_rename_paths(root, new_path, manager, home):
    """Return a validated subtree path plan, including the root document.

    Existing relative suffixes are preserved, including document `.embeds`
    directories. A stale path outside its parent is recoverable only on local
    storage: its stored location must be absent and its exact tree-derived
    location must exist without another record claiming it. No files move here.
    The caller must authorize the root and apply the plan only after its
    storage move succeeds.
    """
    old_root, new_root = _key(root.path), _key(new_path)
    team_root = _key(home["path"], allow_empty=manager.s3_enabled)
    is_home = root.name == home["name"]
    _inside(old_root, team_root)
    if not is_home:
        _inside(new_root, team_root)

    for other in frappe.get_all(
        "Drive File",
        filters={"is_group": 1, "parent_entity": ["is", "not set"]},
        fields=["name", "path", "team"],
    ):
        if not other.path or other.team == root.team:
            continue
        if manager.s3_enabled and manager.get_bucket(other.team) != manager.get_bucket(root.team):
            continue
        other_root = _key(other.path, allow_empty=manager.s3_enabled)
        boundaries = (old_root, new_root)
        if not manager.s3_enabled:
            other_root = manager.resolve(other_root)
            boundaries = tuple(manager.resolve(path) for path in boundaries)
        if any(path.is_relative_to(other_root) or other_root.is_relative_to(path) for path in boundaries):
            frappe.throw("This folder overlaps another team's storage.", frappe.PermissionError)

    if not manager.s3_enabled:
        source_root = manager.resolve(old_root)
        destination_root = manager.resolve(new_root)
        _inside(source_root, manager.resolve(team_root))
        if not is_home:
            _inside(destination_root, manager.resolve(team_root))

    plan, fallbacks, visited = [], [], set()

    def visit(doc, source, destination, depth=0):
        if doc.name in visited or depth > 100:
            _invalid()
        visited.add(doc.name)
        if doc.team != root.team:
            frappe.throw("This folder contains a file from another team.", frappe.PermissionError)
        if not manager.s3_enabled:
            _inside(manager.resolve(source), source_root)
            _inside(manager.resolve(destination), destination_root)
        plan.append((doc, str(source), str(destination)))
        for child in doc.get_children():
            if not child.path or child.is_link or child.mime_type == "frappe/slides":
                continue
            stored = _key(child.path)
            _inside(stored, team_root)
            try:
                relative = stored.relative_to(source)
                if not relative.parts:
                    _invalid()
                actual_source = stored
            except ValueError:
                # Only an exact location implied by this parent can be used.
                # Remote object identity needs separate administrator review.
                if manager.s3_enabled:
                    _invalid()
                title = child.title
                if not title or title in (".", "..") or any(c in title for c in ("/", "\\", "\0")):
                    _invalid()
                relative = Path(".embeds") / title if doc.document else Path(title)
                actual_source = source / relative
                stored_disk = manager.resolve(stored)
                actual_disk = manager.resolve(actual_source)
                _inside(stored_disk, manager.resolve(team_root))
                _inside(actual_disk, source_root)
                if stored_disk.exists() or not actual_disk.exists():
                    _invalid()
                if actual_disk.is_dir() != bool(child.is_group or child.document):
                    _invalid()
                # An alias is not sufficient evidence of this record's bytes.
                probe = manager.site_folder
                for part in actual_source.parts:
                    probe = probe / part
                    if probe.is_symlink():
                        _invalid()
                fallbacks.append((child.name, actual_disk))
            visit(child, actual_source, destination / relative, depth + 1)

    visit(root, old_root, new_root)
    if fallbacks:
        # Include inactive rows: a trashed record must not donate its bytes.
        claims = {}
        for row in frappe.get_all("Drive File", fields=["name", "path"]):
            if row.path:
                try:
                    # Invalid legacy aliases may still claim the same bytes.
                    # Resolve them only for collision detection, never for use.
                    claimed = (manager.site_folder / str(row.path)).resolve()
                    if claimed.is_relative_to(manager.site_folder.resolve()):
                        claims.setdefault(claimed, set()).add(row.name)
                except (ValueError, OSError, RuntimeError):
                    continue
        for doc, source, _ in plan:
            claims.setdefault(manager.resolve(source), set()).add(doc.name)
        for name, source in fallbacks:
            if claims.get(source, set()) - {name}:
                _invalid()
    return [(doc, destination) for doc, _, destination in plan]


def _key(value, allow_empty=False):
    path = Path(str(value or ""))
    if (not value and not allow_empty) or path.is_absolute() or ".." in path.parts or "\0" in str(path):
        _invalid()
    return path


def _inside(path, root):
    if not path.is_relative_to(root):
        frappe.throw("This path leaves the folder's storage boundary.", frappe.PermissionError)


def _invalid():
    frappe.throw(
        "This folder contains an inconsistent or ambiguous file path. "
        "Have a site administrator review its paths before renaming it.",
        frappe.ValidationError,
    )
