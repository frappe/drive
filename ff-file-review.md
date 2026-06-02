# ff-file branch review spec

Working list of issues from the review of `ff-file` vs `develop`. We'll work
through these one at a time. Status legend:

- **open** — to address
- **discuss** — design call needed before action
- **deferred** — known, addressed in a later branch
- **wontfix** — accepted as-is for this PR

---

## Section A — Out of scope for this PR

> Acknowledged as part of this "mega breaking PR" and not in play right now.

### A1. PR bundles three independent migrations
- prettier reformat (every file)
- pnpm → yarn + Vite 4 → 8 + frappe-ui pinned-commit → npm version
- Drive File doctype → framework File doctype

**Status:** wontfix (this PR). For the next big migration, prefer splitting.

---

## Section B — Cleanup once the migration stabilizes

### B1. Parallel `Drive File` implementation is half-renamed and broken
- [drive/drive/doctype/drive_file/drive_file.py](drive/drive/doctype/drive_file/drive_file.py)
  references `self.is_folder` but
  [drive/drive/doctype/drive_file/drive_file.json](drive/drive/doctype/drive_file/drive_file.json)
  still has `is_group` / `is_active`.
- [drive/hooks.py:111](drive/hooks.py#L111) still maps
  `"Drive File": "drive.api.permissions.user_has_permission"`, but the new
  `user_has_permission` assumes a framework `File` doc.

**Decision needed:** delete the `Drive File` doctype + its python class + the
hook entry in a follow-up patch, OR revert the in-place rename in `drive_file.py`
back to `is_group`/`is_active` until removal.

**Status:** deferred — to be removed once the framework-File migration is stable.

---

## Section C — Design questions

> File-as-host is intentional. What we're evaluating is whether the bolting is
> done well.

### C1. Bolting quality — custom fields on `File`

Custom fields added ([drive/fixtures/custom_field.json](drive/fixtures/custom_field.json)):
`is_drive_file`, `team`, `mime_type`, `status`, `file_modified`,
`details_doctype`, `details_docname`.

Concrete points to discuss:

- **`status` (1/0/-1)** shadows the framework's lifecycle (no equivalent
  tombstone field on `File`). OK to have, but worth documenting the state machine
  in one place — currently `1` (active), `0` (trashed), `-1` (permanent-delete
  pending) is implicit and split across `scripts.py`, `overrides/file.py`,
  `list.py`.
- **`details_doctype` / `details_docname`** are functionally a parallel to the
  framework's `attached_to_doctype` / `attached_to_name`. Both are populated by
  [drive/overrides/file.py:after_upload_file](drive/overrides/file.py).
  Either pick one, or document why both exist (e.g. attachments use `attached_to_*`,
  Drive-internal "this File backs a Writer Document / Presentation" uses
  `details_*`).
- **`file_modified`** vs framework `modified`. Currently `FILE_FIELDS` does
  `Coalesce(file_modified, modified) as modified`
  ([drive/utils/__init__.py:101](drive/utils/__init__.py#L101)). Worth a comment
  on *why* drive needs a separate field (touch-without-save?).
- **`is_drive_file` as branch predicate everywhere** —
  `overrides/file.py:only_for_drive_files` and many list/permission paths
  branch on this. Acceptable; just keep the branch points in as few files as
  possible.

**Status:** done.
- `status` Int (1/0/-1) → **Select** `Active`/`Trashed`/`Removed`, default `Active`,
  backed by `STATUS_ACTIVE`/`STATUS_TRASHED`/`STATUS_REMOVED` constants in
  [drive/utils/__init__.py](drive/utils/__init__.py). All numeric comparisons
  replaced across api/utils/overrides (incl. the `if doc.status:` truthiness
  trap in the trash toggle).
- `details_doctype`/`details_docname` → **`content_doctype`/`content_docname`**
  (the record holding the file's actual content — Writer Document, Presentation,
  or referenced library File). Renamed in the fixture and all call sites.
- Data on the `coffee.localhost` dev site migrated in place (status remapped,
  `details_*` copied to `content_*`, orphan columns + custom fields dropped).
- `file_modified` / `is_drive_file` left as-is (acceptable per discussion).

### C2. `file_url` overloading for S3

[drive/utils/files.py:235-258](drive/utils/files.py#L235-L258) — `file_url`
holds three different things:
1. `/private/files/...` for local disk
2. `/api/method/drive.api.s3.fetch?path=...` for S3
3. A literal external URL for Link entries

`sanitize_url`, `get_s3_key`, `get_s3_url` exist to demux. The user has
acknowledged this is badly designed.

**Options to discuss:**

- **(a)** Add a `storage_kind` enum field (`disk` / `s3` / `external`) and a
  separate `storage_key` field — `file_url` becomes a rendered URL only.
- **(b)** Keep `file_url` as the *public* URL form (what a browser hits) and
  reconstruct the S3 key on demand from the entity record (e.g. `team` + `name`
  + a known prefix). Pro: never have to sanitize. Con: needs a deterministic
  key scheme.
- **(c)** Status quo + better helpers + invariant test.

**Status:** done — landed **(c)** (keeping the `file_url` encoding, which matches
the canonical Frappe-S3 pattern, e.g. zerodha/frappe-attachments-s3, and avoids
breaking existing rows) plus a serving fix:
- `sanitize_url` → **`storage_key`**, now always returns a *relative* key so
  `Path(base) / key` can't reset to absolute. Every S3 `Key`/`CopySource` and
  `site_folder` join routes through it (fixed `move`/`move_to_trash` passing the
  raw `file_url` as the S3 key, on both S3 and disk branches).
- `s3.fetch` now serves *through* `get_file_content` (enforces Drive perms per
  request) instead of a second redirect, and is no longer guest-probeable (see D4).
- Invariant test `storage_key(get_s3_url(k)) == k` in
  [drive/tests/test_storage_helpers.py](drive/tests/test_storage_helpers.py).
- Committed in `652dbea2`.

---

## Section D — Bugs (action items, in rough priority order)

### D1. `clear_deleted_files` deletes everything on first run
[drive/api/scripts.py:101](drive/api/scripts.py#L101)
```python
days_before = (date.today() + timedelta(days=30)).isoformat()
result = frappe.db.get_all("File", filters={"status": -1, "modified": ["<", days_before]}, ...)
```
`+ timedelta` should be `-`. As written, `modified < (today + 30 days)` matches
every file with `status == -1`, so the daily job hard-deletes the entire
tombstone bucket immediately.

**Status:** done — already fixed in a prior commit (`scripts.py` now uses
`date.today() - timedelta(days=30)`).

### D2. Migration patch writes the wrong field names
[drive/patches/integrate_with_framework.py:68,76-81](drive/patches/integrate_with_framework.py#L68)
- `"last_modified"` → should be `"file_modified"`
- `special_file` / `special_file_doc` → should be `details_doctype` / `details_docname`

Effect: existing Writer Documents and Presentations migrate without their
backing references; modified timestamps are lost.

**Status:** done — patch now writes `file_modified` and `content_doctype`/
`content_docname` (the renamed C1 fields), and maps `status` to the Select
value. Re-run on staging.

### D3. `auto_delete_expired_perms` removed entirely
Old scheduler entry deleted from [drive/hooks.py:142](drive/hooks.py#L142) and
the function deleted from [drive/api/permissions.py](drive/api/permissions.py).
If `valid_until` is still a field on `Drive Permission`, time-limited shares
now never expire — security regression.

**Status:** done — dropped the feature. `valid_until` was already gone from the
`Drive Permission` doctype and UI; removed the stale write in
[team_restructure.py](drive/patches/team_restructure.py) that was the only
remaining reference.

### D4. `drive.api.s3.fetch` is `allow_guest=True` and probeable
[drive/api/s3.py](drive/api/s3.py)
```python
@frappe.whitelist(allow_guest=True)
def fetch(path: str):
    file = frappe.get_doc("File", {"file_url": get_s3_url(path)})
    ...
```
- Throws `DoesNotExistError` when path is wrong → file existence enumeration.
- No validation that `path` looks like a sane S3 key.
- Permission check is downstream in `get_file_content` (good), but the
  endpoint itself leaks.

**Fix:** return a generic 404 for both "not found" and "no permission"; tighten
`path` validation.

**Status:** done — `fetch` resolves the key, serves through `get_file_content`
(which permission-checks per request), and returns a uniform 404 for both
missing and forbidden so keys can't be enumerated. Committed in `652dbea2`.

### D5. `get_file_content` AttributeError + bad redirect
[drive/api/files.py:364-370](drive/api/files.py#L364-L370)
```python
if file.file_type == "Document" or not file.is_drive_file:
    frappe.local.response["location"] = "/drive/w/" + file.name if file.is_drive_file else file.file_url
    return
if not file or file.file_type in FORBIDDEN_DOWNLOAD_TYPES or file.status != 1:
    frappe.throw("Not found", frappe.DoesNotExistError)
```
- `if not file` check needs to come first.
- Operator precedence: `"/drive/w/" + file.name if file.is_drive_file else file.file_url`
  binds as `"/drive/w/" + (file.name if ... else file.file_url)`. For
  non-drive-files we redirect to `/drive/w/<file_url>` instead of `<file_url>`.

**Status:** done — moved the `not file` guard before the dereference. The
precedence claim was **wrong**: ternary binds looser than `+`, so it already
evaluates as `("/drive/w/" + name) if is_drive else file_url` (verified). Added
parens for clarity.

### D6. `create_presentation` `NameError` on failure path
[drive/api/files.py:196-209](drive/api/files.py#L196-L209)
```python
try:
    r = frappe.call(...)
except BaseException as e:
    print("Couldn't create", e)
entity = create_drive_file(..., lambda _: r.name)
```
- `r` unbound when the call fails.
- `BaseException` catches too much (KeyboardInterrupt, SystemExit).
- `print` instead of `frappe.log_error`.
- `"frappe/slides"` passed as `file_type`, but elsewhere we use `"Presentation"`.

**Status:** moot — `create_presentation` was removed in a prior commit; no
equivalent buggy path remains.

### D7. `entity.file_names` typo crashes embed uploads
[drive/utils/files.py:196](drive/utils/files.py#L196)
```python
return parent / ".embeds" / entity.file_names
```
Should be `entity.file_name`. Hits whenever embed mode is used on non-flat
storage.

**Status:** done — fixed in `652dbea2`.

### D8. `sync_from_disk` broken
[drive/api/scripts.py:65-90](drive/api/scripts.py#L65-L90)
- Passes `is_folder=...` kwarg to `create_drive_file` which has no such
  parameter → `TypeError`.
- Passes lowercase `mime_type` as the positional `file_type` argument, so
  `is_folder = (file_type == "Folder")` is always False even for folders.

**Status:** done — dropped the invalid `is_folder=` kwarg; pass the real
`file_type` (`"Folder"` for folders, else `get_file_type(mime_type)`) and
`mime_type` as the keyword arg.

### D9. `requires` decorator missing return + wrong exception
[drive/api/permissions.py:236-244](drive/api/permissions.py#L236-L244)
- Missing `return fn(...)` — wrapped function's return value is dropped.
- Throws `ValueError` instead of `frappe.PermissionError` for permission
  failures (different HTTP status downstream).

**Status:** done — removed; it was dead code (no callers) referencing the
deprecated `Drive File` doctype.

### D10. `Document.vue` is unreachable
[frontend/src/router.js:161-170](frontend/src/router.js#L161-L170)
The `/w/:entityName` route declares `component: Document.vue` *and* a
`beforeEnter` that hard-redirects to `/writer/w/`. The new 528-line
[frontend/src/pages/Document.vue](frontend/src/pages/Document.vue) is never
rendered.

**Decision needed:** is `Document.vue` meant to replace the `/writer` page,
or is it leftover? If replacing: drop the `beforeEnter`. If leftover: delete
the file.

**Status:** done — leftover. `Document.vue` is already deleted on this branch
and the `/w/` route uses `Dummy` + a redirect to `/writer/w/`.

### D11. `shareView` state shape changed silently
[frontend/src/store.js:32](frontend/src/store.js#L32)
- `shareView: getJson("shareView", "with")` → `shareView: false`
- `toggleShareView` no longer persists to localStorage.

Any component reading `state.shareView === "with"` now compares string to
false. Need to grep call sites and update or restore.

**Status:** done — verified no `"with"` comparisons remain; `shareView` is now a
consistent boolean (false=personal, true=shared). Left the dropped localStorage
persistence as-is (intentional: default to personal view on load).

### D12. `getShared` param name mismatch
[frontend/src/resources/files.js:113](frontend/src/resources/files.js#L113)
sends `shared: true`, but the new endpoint
[drive/api/list.py:shared](drive/api/list.py) takes `shared_type` (string
`"with"` / `"public"`). Verify the default fallback is doing what we want.

**Status:** done — `getShared` now sends `shared_type: 'with'` instead of the
ignored `shared: true`.

### D13. `FileUploader.vue` calls likely-removed endpoints
[frontend/src/components/FileUploader.vue:34,50](frontend/src/components/FileUploader.vue#L34)
- `drive.api.files.does_entity_exist?...&folder=...` — confirm endpoint still
  exists post-migration.
- `drive.api.files.get_new_title?...` — likely renamed to `get_new_file_name`.
- Stray `}` literal in the URL template.

**Status:** done — `does_entity_exist` exists and works; added a whitelisted
`get_new_title` wrapping the `get_new_file_name` util; removed the stray `}`.

### D14. `_get_share_count` parameter is dead, query is unbounded
[drive/api/list.py](drive/api/list.py) — `_get_share_count(team=None)` never
uses `team`. Together with `_get_public_files` and `_get_team_files`, every
list request materializes system-wide permission data. Will not scale.

**Status:** done — all three helpers now take the result-set `names` and filter
`WHERE entity IN (names)`; dropped the dead `team` param.

### D15. `share_count` dict-with-bool-keys trick
[drive/api/list.py:367-371](drive/api/list.py#L367-L371)
```python
r["share_count"] = {
    r["name"] in public_files: -2,
    default > -1 and (r["name"] in team_files): -1,
    default == 0: share_count.get(r["name"], default),
}.get(True, default)
```
Bool keys collide, all RHS computed eagerly, ordering meaningless. Replace
with `if/elif/else`.

**Status:** done — replaced with `if/elif/else` (public > team > default==0),
fixing the silent priority collision.

### D16. `permissions.py` shadows builtin `type`
[drive/api/permissions.py:91](drive/api/permissions.py#L91) — loop variable
renamed from `type_` to `type`. Cosmetic regression.

**Status:** done — already clean; loop uses `type_`, no builtin shadow.

---

## Section E — Smaller / cosmetic

### E1. `print()` calls in production paths
[drive/utils/files.py:229](drive/utils/files.py#L229),
[drive/api/files.py:203](drive/api/files.py#L203). Replace with
`frappe.log_error` / structured logging.

**Status:** done — both prints are gone. The `get_file` one became
`frappe.log_error` earlier (`652dbea2`); the `api/files.py:203` one disappeared
with `create_presentation` (D6, moot).

### E2. `__update_modified` / `__not_if_flat` name mangling
Double-underscore decorators inside the class get name-mangled. Use
single-underscore (`_update_modified`) or move to module scope.
[drive/overrides/file.py:74](drive/overrides/file.py#L74),
[drive/utils/files.py](drive/utils/files.py).

**Status:** done — renamed `__update_modified` → `_update_modified`
([drive/overrides/file.py](drive/overrides/file.py)) and `__not_if_flat` →
`_not_if_flat` ([drive/utils/files.py](drive/utils/files.py)). The copies in the
deprecated `drive_file.py` are left for the B1 deletion.

### E3. `only_for_drive_files` uses `super(type(self), self)`
[drive/overrides/file.py:23-30](drive/overrides/file.py#L23-L30) — fragile if
`File` is ever subclassed further. Use plain `super()`.

**Status:** done — replaced with `super(File, self)` (resolved at call time;
bare `super()` can't be used inside the decorator's `inner`, which has no
`__class__` cell). This also fixes the latent recursion bug `super(type(self),
self)` would cause for a `File` subclass instance.

### E4. `get_attachments` returns synthetic "folder" entities
[drive/api/list.py:359-389](drive/api/list.py#L359-L389) mixes real File rows
with fabricated rows that have `virtual` / `virtual_extra` fields and
`name=<doctype string>`. Frontend
[frontend/src/utils/files.js:24-42](frontend/src/utils/files.js#L24-L42)
special-cases them. Consider a separate endpoint or a tagged-union return type.

**Status:** addressed by the `kind` refactor (see F6) — every row now carries an
explicit `kind`, and the fabricated rows are tagged `kind="virtual"`, so the
frontend tests `e.kind === 'virtual'` instead of sniffing a `virtual` field. The
old overloaded `virtual` ("doctype"/"docname" level) and `virtual_extra` (parent
doctype) fields were replaced with honest `attached_to_doctype` /
`attached_to_name` (mirroring the framework fields these nodes bucket over);
`openEntity` routes on `attached_to_name ? document : doctype`. `FILE_FIELDS`
doesn't carry `attached_to_*`, so there's no collision with real rows. Splitting
`get_attachments` into its own endpoint is still open, but the return shape is
now a clean tagged union keyed on `kind`.

### E5. Hard-coded slides theme
[drive/api/files.py:200](drive/api/files.py#L200) — `theme="1mjgj61m8j"` magic
value. Pull from settings or a constant.

**Status:** moot — gone with `create_presentation` (D6). No `theme=`/magic value
remains in the Python source.

### E6. `details_doctype == "File"` magic string
[drive/api/list.py:381-382](drive/api/list.py#L381-L382),
[drive/api/permissions.py](drive/api/permissions.py) — used in several places
to mean "this is a framework attachment". Wrap in a constant or a helper.

**Status:** done — added `ATTACHMENT_CONTENT_DOCTYPE` and routed
`files.py:redirect_to_original` through it. The `is_attachment`/`modifiable`
booleans were then superseded by the `kind` enum (see F6).

---

## Section F — Senior engineer feedback

### F1. Validate and enforce `is_private` for drive files
[drive/overrides/file.py:66-67](drive/overrides/file.py#L66-L67) — `set_is_private`
only sets the flag once; nothing prevents a later `db_set`/`save` from flipping
it to `0`, which would expose the file via `/files/...`.

**Fix:** in `validate` (drop the no-op `pass`, gate on `is_drive_file`),
throw if `is_private != 1`. Also harden `after_upload_file` to set
`is_private = 1` on the framework branch when the upload routes through Drive.

**Status:** done — `validate` (drive branch) now throws `ValidationError` if
`is_private` is falsy on save. `after_upload_file` sets `is_private = 1` on
both the library-copy branch and the `use_drive_for_files` branch.
[drive/overrides/file.py](drive/overrides/file.py).

### F2. Upload routing when "use Drive for files" is on

When `Drive Disk Settings.use_drive_for_files = 1`, framework uploads
(`after_upload_file` in [drive/overrides/file.py:340-371](drive/overrides/file.py#L340-L371))
route through Drive. Two gaps:

- **F2a. Default destination.** No default; current path is
  `private/files/<doctype>/<docname>/<filename>`. Senior asks for: default
  to the uploading user's attachments folder (e.g.
  `Home/Attachments/<user>/...` or similar — TBD schema). Open: where
  exactly, and is the user folder auto-created on first upload?
- **F2b. Allow user to choose at upload time.** Currently no picker.
  Need a Vue picker that surfaces during the stock framework upload flow.

**Status:** F2a done (needs verification); F2b deferred.
- **F2a** — the `use_drive_for_files` branch in `after_upload_file` previously
  set `is_drive_file = 1` but never set `team`/`folder`, so the attachment was
  orphaned (Drive list views filter by `team`, so it was invisible). It now
  defaults to the uploading user's personal Drive home folder, **guarded**: when
  there is no personal team (system / guest / background uploads), it falls back
  to the un-placed attachment instead of throwing and blocking the upload.
  [drive/overrides/file.py](drive/overrides/file.py).
- **F2b** (destination picker) and a dedicated `Attachments` subfolder + aligning
  the on-disk path with the team storage tree remain the design pass — deferred.

### F3. Splice Drive's own component into the stock upload dialog
[drive/public/js/ff_integration.bundle.js:5-41](drive/public/js/ff_integration.bundle.js#L5-L41) —
`DRIVE_UPLOADER` is half-wired; the `UploadOptions.push` line is commented
out and the body uses a placeholder `FileUploader.vue`.

**Direction (per feedback):** *replace* the stock "Library" (second) tab in
`frappe.ui.FileUploader` with a clean Drive Vue component. The component
should show, in tabs:

- the uploading user's **Home folder** (and subfolders)
- the **site** scope (shared Drive root)
- each **team** the user belongs to

Each tab acts as a folder picker; choosing a destination either copies an
existing file in (current behavior) or sets the destination folder for a
fresh upload (ties into F2b).

**Status:** done (additional-button form) — **needs manual verification on a
running desk** (dev site currently down, tests disabled). Registered
`DRIVE_UPLOADER` into `frappe.ui.FileUploader.UploadOptions` as a "Drive" button
— the supported, non-fragile extension point. *Replacing* the stock Library tab
would mean patching framework `FileUploader.vue` from an app, which is fragile;
rejected. Selecting a Drive file routes through the framework's
`library_file_name` flow, which `after_upload_file` already turns into an
attachment pointing back at the chosen file (`content_doctype`/`content_docname`).
Fixed the prior bugs (undeclared `file`, ref access, the `file_url` hack) and
guarded against double-registration.
[drive/public/js/ff_integration.bundle.js](drive/public/js/ff_integration.bundle.js).

### F4. Customize the framework `File` desk form
"Attached to — flatten, move to bottom" (framework File desk form).

**Fix:** add a Customize Form / Property Setter fixture that:

- moves `attached_to_doctype` + `attached_to_name` to the bottom of the form
- removes their section/column break wrapping (flatten)
- sits below the `Drive Properties` section added by
  [drive/fixtures/custom_field.json](drive/fixtures/custom_field.json)

**Status:** not done (reverted). A first pass added a `property_setter.json`
fixture + enabled the `fixtures` hook, but that was backed out: a Property Setter
is the *only* app-level way to move a standard `File` field, but it's heavier
than warranted, and the form's real problem is the buggy custom-field chain (see
below), not a missing setter. The cleaner fix — if pursued — is to repair the
`insert_after` chain in `custom_field.json` and anchor the `Drive Properties`
section just before `section_break_8` (`insert_after: is_folder`), so the form
renders …fields → Drive Properties → Attached To with no Property Setter. Left as
a deliberate non-change for now.

Bugs noticed in [drive/fixtures/custom_field.json](drive/fixtures/custom_field.json)
(layout only — columns still exist): `mime_type` → `insert_after: "drive_team"`
(no such field; should be `team`), `column_break_tapww` →
`insert_after: "settings"` (no such field), and the `Drive Properties` section is
anchored on `section_break_8` so it renders jammed inside the Attached To section.

> **Important (separate, real migration concern — independent of F4):** the
> `fixtures` hook was commented out, so `custom_field.json` / `role.json` never
> synced — the custom fields existed on the dev site only because they were
> hand-created. **Re-enabled** the hook for `Custom Field` (File) + Drive `Role`
> in [drive/hooks.py](drive/hooks.py) (Property Setter dropped). **Remaining
> caveat:** fixtures sync *after* post_model_sync patches, but
> `integrate_with_framework` writes to those columns during post_model_sync — so
> on a fresh migrate the columns still won't exist when the patch runs (the
> `Unknown column 'team'` family of error). Create the custom fields early
> (`create_custom_fields(...)` in a pre_model_sync patch or at the top of the
> integrate patch). Also `install.py:after_install` still references
> `tabDrive File` and will fail on a fresh install.

### F5. Verify framework rename works on Drive files
The override exposes its own [drive/overrides/file.py:rename](drive/overrides/file.py#L276)
(whitelisted, used by the Drive UI). But the framework also offers rename
via `frappe.rename_doc` and the desk title-edit affordance. Two things to
verify:

- Does standard desk rename of a drive `File` row trigger the disk/S3
  move? It shouldn't go through `self.manager.rename(self)` today.
- If we rename a drive file from the desk, do permissions check via
  `user_has_permission`, or does it bypass via framework's default rename
  permissions?

**Fix (likely):** intercept rename for `is_drive_file == 1` (either via
`after_rename` doc event or by overriding the framework's rename code
path) so the same logic as `overrides/file.py:rename` runs.

**Status:** done.
- **Permissions:** the `has_permission` hook was registered under the dead
  `"Drive File"` doctype, so framework `File` rows bypassed Drive's ACL on the
  desk. Re-pointed to `"File"` in [drive/hooks.py](drive/hooks.py). Safe because
  `user_has_permission` delegates non-drive Files to the framework's own check
  (`ff_has_permission`), so attachments are unaffected.
  (`permission_query_conditions` for list/report still points at `"Drive File"`
  and queries `tabDrive File` — left as B1 deferred cleanup.)
- **Disk move:** a desk-side `file_name` edit persisted the new name without
  moving the blob (stale `file_url`). Replicating the move inside `validate` is
  unsafe (`recursive_path_move` calls `save()` → recursion), so out-of-band
  renames are now **blocked** in `validate` and must go through the Drive UI; the
  sanctioned `rename`/`move` methods set `flags.drive_disk_rename` to bypass.
  [drive/overrides/file.py](drive/overrides/file.py). (Primary-key renames via
  `frappe.rename_doc` are an unusual admin op and left as-is.)

### F6. UX parity: drive-native vs attachment, inside Drive
Inside the Drive frontend, a drive-native file and a framework attachment
(both real `File` rows) should look and behave the same wherever possible.
Current gaps:

- `modifiable` / `is_attachment` flags set by
  [drive/api/list.py:378-379](drive/api/list.py#L378-L379) gate writes; UI
  surfaces them as "read-only" attachments.
- Preview/share/rename/move actions are partially disabled for attachments
  in components like
  [frontend/src/components/InfoPopup.vue](frontend/src/components/InfoPopup.vue)
  and
  [frontend/src/components/ContextMenu.vue](frontend/src/components/ContextMenu.vue)
  (audit needed).
- Thumbnail generation for attachments — does `after_upload_file` enqueue
  it? Quick read says no (`create_thumbnail=False` at
  [drive/overrides/file.py:369](drive/overrides/file.py#L369)).

**Fix:** audit every Drive UI action and either enable it for attachments
or document why it's not safe (e.g. rename would break the host record's
`file_url`). Where safe, enable. Where not safe, surface a clear reason.
Thumbnails should be on by default.

**Status:** done — **also reworked the underlying model** (the
`modifiable`/`is_attachment` booleans were vague and overlapping).

**`kind` enum** — every Drive listing row now carries one self-documenting,
mutually-exclusive `kind` (`entity_kind()` in
[drive/utils/__init__.py](drive/utils/__init__.py); set in
`list.py:get_query_data`, the `get_attachments` virtual rows, and
`permissions.py:get_entity_with_permissions`):
- `native` — Drive owns identity & storage (incl. folders, Writer Documents,
  Presentations). Was `modifiable=1`.
- `reference` — a Drive row pointing at another framework File ("open original").
  Was `is_attachment=1`.
- `foreign` — a stock framework File shown read-only in Drive ("open in desk").
- `virtual` — fabricated grouping node (Doctype→Doc tree). Folds in the old
  `!e.virtual` checks (also addresses E4).

The frontend gates now read intent directly (`GenericPage.vue`, `Navbar.vue`,
`InfoPopup.vue`): rename/move/share → `kind === 'native'`, open-original →
`kind === 'reference'`, open-in-desk → `kind === 'foreign'`, etc. Verified on
`coffee.localhost` (all four kinds derive correctly; no `modifiable`/
`is_attachment` keys leak into responses).

Per-action decisions:
- **Download** — was wrongly gated on `modifiable`, so attachments couldn't be
  downloaded. Now allowed for any real file (`kind !== 'virtual'` + downloadable
  type), matching the file-preview navbar. (Also fixed a regression where my
  first F6 pass let Download appear on virtual folders.) **Safe — enabled.**
- **Copy Link / Show Info / Go to original** — enabled.
- **Rename / Move** — `kind === 'native'` only: on a `reference`/`foreign` row
  they'd rewrite the on-disk path / `file_url` and orphan the host blob.
  **Documented unsafe.**
- **Share** — `kind === 'native'` only: a framework attachment is shared via its
  host document, not as a standalone Drive entity. **Documented.**
- **Thumbnails** — `after_upload_file` no longer passes `create_thumbnail=False`;
  back to the default (enqueued, image/video/pdf only).
  [drive/overrides/file.py](drive/overrides/file.py).

### F7. `move` does not write an activity log entry
[drive/overrides/file.py:194](drive/overrides/file.py#L194) `move` mutates
location and calls `__update_modified`, but does not call
`create_new_activity_log` the way `rename` does
([line 289](drive/overrides/file.py#L289)). Move history is invisible in the
activity sidebar.

**Fix:** add an activity log entry mirroring rename — `activity_type="move"`,
`field_old_value=old_folder_name`, `field_new_value=new_folder_name`,
message `"<user> moved <file_name> to <new_folder_name>"`.

**Status:** done — `move` now writes a `move` activity log (old/new folder
*names*, `document_field="folder"`, message `"<user> moved <file> to <folder>"`)
inside the `new_parent != self.folder` block, before the folder mutation.
[drive/overrides/file.py](drive/overrides/file.py).
