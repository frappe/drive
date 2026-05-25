# Analytics Plan: Frappe Drive

## Product reasoning
- **Primary value:** Store, access, and share files and documents from a single organised place (self-hosted Drive/Dropbox alternative).
- **Activation behaviours:** Signup → personal team auto-created (Setup.vue) → first file uploaded or document created → that file opened. A user who has uploaded *and* opened at least one file has experienced the core loop.
- **Retention behaviours:** A user who returns to open a file or run a search has mentally "stored" things in Drive and is coming back to retrieve them. `track_visit` + search are the two clearest signals. Favouriting is a secondary indicator (they care enough to bookmark).
- **Collaboration behaviours:** Sharing a file/folder with another person (ShareDialog), copying a public link, or inviting someone to a team. Team creation alone is not collaboration — the trigger is the first share or invite *sent*.

---

## Core signals

### Onboarding
| Action | Location | Notes |
|--------|----------|-------|
| OTP verified | `drive/api/product.py::verify_otp` | `req.login_count` increments; first call == login gate passed |
| Signup completed | `drive/api/product.py::signup` | `account_request.signed_up = 1`; user record created |
| Personal team created | `drive/drive/doctype/drive_team/drive_team.py::after_insert` | Triggered automatically from `Setup.vue::createTeam(personal=1)` on first login — marks app ready to use |
| First file uploaded | `drive/api/files.py::upload_file` | Activation: user has put something of value into Drive |
| First document created | `drive/api/files.py::create_document_entity` | Activation via the doc-creation path |
| Invite accepted (new user) | `drive/drive/doctype/drive_user_invitation/drive_user_invitation.py::accept` | A viral signup; `status → Accepted` |

### Engagement
| Action | Location | Notes |
|--------|----------|-------|
| File uploaded | `drive/api/files.py::upload_file` | Include `mime_type`, `file_size`; exclude `embed=1` and `transfer=1` from the main event |
| Document created | `drive/api/files.py::create_document_entity` | |
| File opened / viewed | `drive/api/permissions.py::get_entity_with_permissions` | Called by both `File.vue` and `Folder.vue`; calls `mark_as_viewed` internally; include `file_type` |
| File downloaded | `drive/api/files.py::get_file_content` | Only when `trigger_download=True`; include `mime_type` |
| Search performed | `drive/api/files.py::search` | Emit query length + result count (never raw query text); also triggered from `SearchPopup.vue` |

### Retention
| Action | Location | Notes |
|--------|----------|-------|
| File revisited | `drive/api/files.py::track_visit` | Writes to `Drive Entity Log`; already exists — hook here for Pulse; best daily-active signal |
| File favourited | `drive/api/files.py::set_favourite` (or `DriveFile.toggle_favourite`) | `is_favourite=True` path only |

### Collaboration
| Action | Location | Notes |
|--------|----------|-------|
| File / folder shared with user | `drive/drive/doctype/drive_file/drive_file.py::share` | User path (`user != ""`); include access level granted |
| File / folder made public | `drive/drive/doctype/drive_file/drive_file.py::share` | `user=""` path (general access = public/team) |
| Public link copied | `ShareDialog.vue::getLink()` | Frontend-only; calls `drive.utils.files.getLink`; no backend counterpart — instrument frontend |
| User invited to team | `drive/api/product.py::invite_users` | Email sent; `UserListSettings.vue` is the entry point |
| Team invite accepted | `drive/drive/doctype/drive_user_invitation/drive_user_invitation.py::accept` | `status → Accepted` |
| Team created (non-personal) | `drive/api/product.py::create_team` | `personal=0`; intent to organise with others |

---

## Feature buckets

### Tags
| Action | Location | Notes |
|--------|----------|-------|
| Tag created | `drive/api/tags.py::create_tag` | |
| Tag added to file | `drive/api/tags.py::add_tag` | |
| Tag removed from file | `drive/api/tags.py::remove_tag` | |

### File organisation
| Action | Location | Notes |
|--------|----------|-------|
| Folder created | `drive/api/files.py::create_folder` | Also available inline in `MoveDialog.vue` |
| File / folder moved | `drive/api/files.py::move` | `MoveDialog.vue` and sidebar drag-and-drop |
| File / folder renamed | `drive/drive/doctype/drive_file/drive_file.py::rename` | Already writes a `Drive Entity Activity Log` entry |
| Folder colour changed | `drive/drive/doctype/drive_file/drive_file.py::change_color` | |
| Link (URL bookmark) created | `drive/api/files.py::create_link` | |

### Trash / deletion
| Action | Location | Notes |
|--------|----------|-------|
| File trashed | `drive/api/files.py::remove_or_restore` | `is_active 1 → 0` |
| File restored from trash | `drive/api/files.py::remove_or_restore` | `is_active 0 → 1` |
| File permanently deleted | `drive/api/files.py::delete_entities` | |

### Quick Transfer
| Action | Location | Notes |
|--------|----------|-------|
| Transfer file sent | `drive/api/files.py::upload_file` with `transfer=1` | Ephemeral device-to-device share via `/transfer` (QuickShare.vue) |
| Transfer file downloaded | `QuickShare.vue::entitiesDownload` | Frontend-only; backend uses same `get_file_content` |

### Notifications
| Action | Location | Notes |
|--------|----------|-------|
| Notification clicked | `Notifications.vue::onRowClick` | Frontend; marks as read and routes to entity |
| All notifications marked read | `drive/api/notifications.py::mark_as_read` with `all=True` | |

### Settings & preferences
| Action | Location | Notes |
|--------|----------|-------|
| User preference changed | `drive/api/product.py::set_settings` | `single_click`, `auto_detect_links`, `default_team`; emit which key changed, not the value |
| Team member role changed | `drive/api/product.py::set_user_access` | Admin action; include new `access_level` |
| Download toggle changed | `drive/api/permissions.py::toggle_allow_download` | Public file download on/off |

### Storage & admin
| Action | Location | Notes |
|--------|----------|-------|
| Storage breakdown viewed | `drive/api/storage.py::storage_breakdown` | User checking usage |
| Sync from disk triggered | `drive/api/scripts.py::sync_from_disk` | Admin / power-user action |

---

## State transitions
| Doctype | Field | Values | Proposed event name |
|---------|-------|--------|---------------------|
| Drive File | `is_active` | `1 → 0` (trashed), `0 → 1` (restored), `is_active = -1` (permanent delete) | `drive_file_trashed`, `drive_file_restored`, `drive_file_deleted` |
| Drive User Invitation | `status` | `Pending → Accepted`, `Pending → Expired`, `Proposed → Accepted` | captured in `invite_accepted` / `invite_expired` |
| Drive Comment | `resolved` | `0 → 1` | `drive_comment_resolved` |
| Drive Notification | `read` | `0 → 1` | captured in notifications feature bucket above |

---

## Frontend workflows

### Core routes (page views worth tracking)
| Route | Why it's core |
|-------|--------------|
| `/` (Home) | Primary browse surface — most file access starts here |
| `/f/:entityName` (File) | File view — direct measure of content consumption |
| `/d/:entityName` (Folder) | Folder navigation — measures depth of use |
| `/w/:entityName` (Document) | Document open — redirects to Writer; track exit intent from Drive |

### In-app workflows
Meaningful interactions within pages — not navigation.

| Workflow | Component | Trigger | Backend counterpart |
|----------|-----------|---------|---------------------|
| Upload file | `Navbar` / `SearchPopup.vue` | "Upload File" button or drag-drop | `drive.api.files.upload_file` |
| Create document | `Navbar` context menu | "New Document" CTA | `drive.api.files.create_document_entity` |
| Create folder | `NewFolderDialog.vue` | "New Folder" dialog confirm | `drive.api.files.create_folder` |
| Share file / folder | `ShareDialog.vue` | "Invite" button or general-access dropdown | `drive.api.files.update_access` |
| Copy public link | `ShareDialog.vue::getLink` | "Copy Link" button | none (frontend util) |
| Move file | `MoveDialog.vue` | "Move" confirm button | `drive.api.files.move` |
| Search | `SearchPopup.vue` | Sidebar search item or keyboard shortcut | `drive.api.files.search` |
| Invite team member | `UserListSettings.vue` | "Send Invitation" dialog | `drive.api.product.invite_users` |
| Create team | `UserListSettings.vue` | "New Team" dialog confirm | `drive.api.product.create_team` |
| Accept / reject invite | `UserListSettings.vue` | Accept/reject buttons in alert | `drive.api.product.accept_invite` / `reject_invite` |
| Quick transfer | `QuickShare.vue` | "Transfer" button | `drive.api.files.upload_file` (transfer=1) |
| Mark all notifications read | `Notifications.vue` | "Mark all as Read" button | `drive.api.notifications.mark_as_read` |
| Drag file to trash or team | `Sidebar.vue::handleDrop` | Sidebar drag-and-drop | `drive.api.files.move` or `remove_or_restore` |

---

## Uninstrumented gaps
- **Collaborative document editing** — `Drive Document.settings` has `{"collab": true}` but the collab session is entirely inside the separate Writer app; no Drive hook when a second user joins.
- **Public/guest file views** — `get_entity_with_permissions` serves guests but there is no telemetry path for anonymous consumption.
- **Storage threshold crossing** — `storage_bar_data` runs on every upload; no event fires when a team crosses 80% or 100% of quota.
- **Embed creation** — `upload_file` with `embed=1` is functionally a separate action (inline attachment) but shares the same API endpoint with no distinct event.
- **Full-screen file preview** — `File.vue::enterFullScreen` is a meaningful engagement depth signal with no backend counterpart.
- **Keyboard shortcut usage** — sidebar `accessKey` hints and `onKeyStroke` bindings in `File.vue` have no tracking.
- **Team `public` flag** — making an entire team public is a direct save on `Drive Team.public`; no dedicated API call.
