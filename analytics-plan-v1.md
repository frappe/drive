# Analytics Plan: Frappe Drive

## App
- Name: drive
- Core doctypes: Drive File, Drive Team, Drive Document, Drive Permission, Drive User Invitation, Drive Tag, Drive Favourite, Drive Entity Log, Drive Notification, Drive Comment

---

## Onboarding signals
Actions that mark a user reaching activation for the first time.

| Action | Location | Notes |
|--------|----------|-------|
| OTP verified (first login) | `drive/api/product.py::verify_otp` | `req.login_count` increments here; first call is activation |
| Signup completed | `drive/api/product.py::signup` | `account_request.signed_up = 1`, user created, first personal team implied |
| Invite accepted | `drive/drive/doctype/drive_user_invitation/drive_user_invitation.py::accept` | `status → "Accepted"` is the clearest join moment |
| First file uploaded | `drive/api/files.py::upload_file` | Can check Drive File count == 1 for user |
| First document created | `drive/api/files.py::create_document_entity` | Creates a `Drive Document` + `Drive File` with mime `frappe_doc` |
| First folder created | `drive/api/files.py::create_folder` | User organising content |

---

## Engagement signals
Feature depth — things users do when they're getting value.

| Action | Location | Notes |
|--------|----------|-------|
| File uploaded | `drive/api/files.py::upload_file` | Emit with `mime_type`, `file_size`, whether it's a transfer or embed |
| Folder created | `drive/api/files.py::create_folder` | |
| Link created | `drive/api/files.py::create_link` | Bookmarking external URLs inside Drive |
| Document created | `drive/api/files.py::create_document_entity` | |
| File renamed | `drive/drive/doctype/drive_file/drive_file.py::rename` | Already writes activity log entry — good companion |
| File moved | `drive/api/files.py::move` | Can include cross-team moves |
| File downloaded | `drive/api/files.py::get_file_content` | Only when `trigger_download=True` |
| File viewed (open) | `drive/api/permissions.py::get_entity_with_permissions` | Calls `mark_as_viewed` internally; file type available |
| Search performed | `drive/api/files.py::search` | Emit query length + result count (never raw query) |
| Tag created | `drive/api/tags.py::create_tag` | |
| Tag added to file | `drive/api/tags.py::add_tag` | |
| Tag removed from file | `drive/api/tags.py::remove_tag` | |
| Folder colour changed | `drive/drive/doctype/drive_file/drive_file.py::change_color` | Cosmetic personalisation signal |
| Quick transfer used | `drive/api/files.py::upload_file` with `transfer=1` | Ephemeral share — `/transfer` route |
| Sync from disk | `drive/api/scripts.py::sync_from_disk` | Power-user / admin action |
| Storage breakdown viewed | `drive/api/storage.py::storage_breakdown` | User checking usage |

---

## Collaboration signals
Social and sharing actions.

| Action | Location | Notes |
|--------|----------|-------|
| File/folder shared with user | `drive/drive/doctype/drive_file/drive_file.py::share` | Emit access level granted (read/write/comment/upload/share) |
| File/folder made public | `drive/drive/doctype/drive_file/drive_file.py::share` | `user=""` path |
| File/folder shared with team | `drive/drive/doctype/drive_file/drive_file.py::share` | `team=True` path |
| File/folder unshared | `drive/drive/doctype/drive_file/drive_file.py::unshare` | |
| Download toggled | `drive/api/permissions.py::toggle_allow_download` | Allows guests to download public files |
| User invited to team | `drive/api/product.py::invite_users` | Email invite sent |
| Invite accepted | `drive_user_invitation.py::accept` | User joins team |
| Team created | `drive/api/product.py::create_team` | `personal=0` is collaboration intent |
| User role changed | `drive/api/product.py::set_user_access` | `access_level` change (guest/member/admin) |
| User removed from team | `drive/api/product.py::remove_user` | |
| User left team | `drive/api/product.py::leave_team` | |

---

## Retention signals
What brings users back. Note any existing logging that can be reused.

| Action | Location | Notes |
|--------|----------|-------|
| File visit tracked | `drive/api/files.py::track_visit` | Already writes to `Drive Entity Log` — reuse this hook |
| Favourite added | `drive/api/files.py::set_favourite` | `is_favourite=True` path |
| Favourite removed | `drive/api/files.py::set_favourite` | `is_favourite=False` path |
| Notifications read | `drive/api/notifications.py::mark_as_read` | `all=True` vs single |
| Recents cleared | `drive/api/files.py::remove_recents` | |

---

## State transitions
Doctype fields worth tracking on change.

| Doctype | Field | Values | Proposed event name |
|---------|-------|--------|---------------------|
| Drive File | `is_active` | `1` (active) → `0` (trashed) → `-1` (permanently deleted) | `drive_file_trashed`, `drive_file_restored`, `drive_file_deleted` |
| Drive User Invitation | `status` | `Pending → Accepted`, `Pending → Expired` | `drive_invite_accepted`, `drive_invite_expired` |
| Drive Comment | `resolved` | `0 → 1` | `drive_comment_resolved` |
| Drive Permission | `read/write/comment/upload/share` | any change | captured in `share` event above |

---

## Frontend workflows
| Route | What the user is doing |
|-------|----------------------|
| `/signup` | Completing account creation |
| `/login` | Authenticating |
| `/setup` | First-time app setup |
| `/` (Home) | Browsing personal files |
| `/inbox` | Reading notifications |
| `/teams` | Managing team membership |
| `/shared` | Browsing files shared with or by me |
| `/recents` | Reviewing recently accessed files |
| `/favourites` | Accessing bookmarked files |
| `/documents` | Browsing Frappe Docs |
| `/presentations` | Browsing slides/presentations |
| `/trash` | Managing deleted files |
| `/transfer` | Ephemeral quick-share |
| `/t/:team/` | Browsing a specific team's drive |
| `/f/:entityName` | Viewing/previewing a file |
| `/d/:entityName` | Navigating a folder |
| `/w/:entityName` | Opening a document in Writer |

---

## Uninstrumented gaps
Features visible in code with no natural tracking point yet.

- **Collaborative editing** — `Drive Document.settings` has `{"collab": true}` but there is no hook when a second user joins a collab session; this is entirely in the Writer app.
- **Guest/public file access** — `get_entity_with_permissions` serves guests but there is no telemetry path for anonymous views.
- **Storage milestone** — the `storage_bar_data` check runs on every upload but there is no event when a team crosses a usage threshold (e.g. 80%).
- **File preview types** — `get_thumbnail` is called per file type but nothing records which MIME types are actually previewed.
- **Embed creation** — `upload_file` with `embed=1` is not distinguishable from a normal upload without an explicit event.
- **Team `public` flag toggle** — making a whole team public/private is not surfaced via a dedicated API call (direct doc save).
