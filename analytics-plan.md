# Analytics Plan: Frappe Drive

## Product reasoning

- **Primary value:** Store, organize, and share files and rich-text documents with teammates — the value is delivered the moment a user successfully creates, views, or receives a shared file.
- **Activation behaviours:** (1) User uploads their first file OR creates their first document; (2) User opens a file that someone shared with them; (3) User shares a file with at least one other person.
- **Retention behaviours:** User returns across sessions to upload, view, or edit files; user is part of an active team; user has favourited items (bookmark proxy for "this is my workspace").
- **Collaboration behaviours:** Sharing a file/folder with another user; inviting someone to a team; file is accessed by someone other than the owner.

---

## Core signals

### Onboarding

| Action | Location | Notes |
|--------|----------|-------|
| User signs up (OTP flow) | `drive.api.product.signup` | Marks new user; capture `has_invite` to split organic vs invited |
| User verifies OTP for login | `drive.api.product.verify_otp` | Captures returning logins too — distinguish with `is_new_user` |
| Setup page visited | `/setup` route | Bridge between signup and first meaningful action |
| First file uploaded | `drive.api.files.upload_file` | `is_first=True` if user has no other Drive Files |
| First document created | `drive.api.files.create_document_entity` | Rich-text doc creation |
| First folder created | `drive.api.files.create_folder` | Folder structure = user understanding org |

### Engagement

| Action | Location | Notes |
|--------|----------|-------|
| File uploaded | `drive.api.files.upload_file` | mime_type, file_size, team |
| Document created | `drive.api.files.create_document_entity` | team |
| Folder created | `drive.api.files.create_folder` | team |
| File/folder opened (view) | `drive.api.files.track_visit` (already called) | Capture entity_type, mime_type |
| File previewed in-app | `File.vue` onSuccess | file_type, mime_type |
| File downloaded | `drive.api.files.get_file_content` when `trigger_download=True` | mime_type, file_size |
| Search performed | `drive.api.files.search` | query length, results_count |
| File renamed | `drive.api.files.rename` | entity_type |
| File moved | `drive.api.files.move` | cross-team move flag |
| File trashed | `drive.api.files.remove_or_restore` when moving to trash | entity_type |

### Retention

| Action | Location | Notes |
|--------|----------|-------|
| File favourited | `drive.api.files.set_favourite` (add path) | entity_type |
| Recents visited | `/recents` route | Proxy for "came back to continue work" |
| File restored from trash | `drive.api.files.remove_or_restore` when restoring | entity_type |

### Collaboration

| Action | Location | Notes |
|--------|----------|-------|
| File shared with user | `DriveFile.share` / `drive.api.files.update_access` | share_method (user/team/public), access_level |
| File unshared | `drive.api.files.update_access` method=unshare | |
| User invited to team | `drive.api.product.invite_users` | as_guest, team |
| Team created | `drive.api.product.create_team` | personal flag |
| Share notification sent | `drive.api.notifications.notify_share` | entity_type |
| Shared file accessed by non-owner | `drive.api.permissions.get_entity_with_permissions` when owner≠user | entity_type |

---

## Feature buckets

### Tags

| Action | Location | Notes |
|--------|----------|-------|
| Tag created | `drive.api.tags.create_tag` | color |
| Tag added to file | `drive.api.tags.add_tag` | |
| Tag removed from file | `drive.api.tags.remove_tag` | |

### Quick Share / Transfer

| Action | Location | Notes |
|--------|----------|-------|
| Transfer uploaded | `drive.api.files.upload_file` with `transfer=1` | file_size |
| Transfer page visited | `/transfer` route | |

### Embeds

| Action | Location | Notes |
|--------|----------|-------|
| Embed accessed | `drive.api.embed.get_file_content` | |

### Notifications

| Action | Location | Notes |
|--------|----------|-------|
| Notification read | `drive.api.notifications.mark_as_read` | all vs single |
| Inbox visited | `/inbox` route | |

### Settings

| Action | Location | Notes |
|--------|----------|-------|
| User settings updated | `drive.api.product.set_settings` | which setting changed |
| Disk settings configured | `drive.api.product.disk_settings` (POST) | backend_type |

---

## State transitions

| Doctype | Field | Values | Proposed event name |
|---------|-------|--------|---------------------|
| Drive File | `is_active` | 1 → 0 (trash) | `drive_file_trashed` |
| Drive File | `is_active` | 0 → 1 (restore) | `drive_file_restored` |
| Drive User Invitation | `status` | Pending → Accepted | `drive_invite_accepted` |
| Drive User Invitation | `status` | Pending → Expired | `drive_invite_rejected` |

---

## Frontend workflows

### Core routes (page views worth tracking)

| Route | Why it's core |
|-------|--------------|
| `/` (Home/Personal) | Entry point for personal files — DAU proxy |
| `/t/:team` (Team) | Entry point for collaborative work |
| `/f/:entityName` (File) | File preview — consumption signal |
| `/d/:entityName` (Folder) | Folder navigation — depth-of-use signal |
| `/shared` | Collaboration surface — shared-with-me signal |
| `/recents` | Return-to-work retention signal |

### In-app workflows

| Workflow | Component | Trigger | Backend counterpart |
|----------|-----------|---------|---------------------|
| Upload file | `GenericPage.vue` / drag-drop zone | File drop or file picker | `drive.api.files.upload_file` |
| Create document | Navbar new-doc button | Click | `drive.api.files.create_document_entity` |
| Create folder | `NewFolderDialog.vue` | New folder dialog submit | `drive.api.files.create_folder` |
| Share file/folder | `ShareDialog.vue` | Share action in toolbar/context menu | `drive.api.files.update_access` |
| Invite user via share | `ShareDialog.vue` addShares() | "Invite" button | `drive.api.product.invite_users` |
| Download file | `GenericPage.vue` actionItems | Download action | `drive.api.files.get_file_content` |
| Rename | `RenameDialog.vue` | Rename action | `drive.api.files.rename` |
| Move | `MoveDialog.vue` / drag-drop | Move action or drop onto folder | `drive.api.files.move` |
| Trash | `GenericPage.vue` actionItems | Delete action | `drive.api.files.remove_or_restore` |
| Favourite | `GenericPage.vue` actionItems | Star action | `drive.api.files.set_favourite` |
| Search | `SearchPopup.vue` | Cmd+K or search bar | `drive.api.files.search` |
| Copy link | `GenericPage.vue` actionItems | Copy link action | (client-side only) |

---

## Uninstrumented gaps

- **File preview keyboard navigation** (Shift+Arrow in `File.vue`) — skipped intentionally for now.

---

## Event map

### Backend

| Event name | Doctype / Method | Hook | Extra properties | Approach |
|------------|-----------------|------|-----------------|----------|
| `drive_user_signed_up` | `drive.api.product.signup` | after `frappe.local.login_manager.login_as` succeeds | `has_invite: bool` | `frappe.utils.telemetry.capture` in `signup()` |
| `drive_user_logged_in` | `drive.api.product.verify_otp` | after `login_as` on existing user | `is_new_user: bool` | capture in `verify_otp()` |
| `drive_file_uploaded` | `drive.api.files.upload_file` | at end of function, after `drive_file` is ready | `mime_type`, `file_size`, `is_transfer: bool`, `is_embed: bool`, `team` | capture before `return drive_file` |
| `drive_document_created` | `drive.api.files.create_document_entity` | at end | `team` | capture before `return entity` |
| `drive_folder_created` | `drive.api.files.create_folder` | at end | `team` | capture before `return drive_file` |
| `drive_link_created` | `drive.api.files.create_link` | at end | `team` | capture before `return drive_file` |
| `drive_file_shared` | `drive.drive.doctype.drive_file.drive_file.DriveFile` `share` method | after share permission is saved | `access_level`, `share_method` (user/team/public), `entity_type` | capture in `DriveFile.share()` or `update_access()` |
| `drive_file_downloaded` | `drive.api.files.get_file_content` | when `trigger_download=True`, after sending file | `mime_type`, `file_size` | capture at top of `get_file_internal()` when `trigger_download` |
| `drive_file_trashed` | `drive.api.files.remove_or_restore` | when `flag=0` (trashing) | `entity_type` (file/folder/document) | capture inside `depth_zero_toggle_is_active` |
| `drive_file_restored` | `drive.api.files.remove_or_restore` | when `flag=1` (restoring) | `entity_type` | capture inside `depth_zero_toggle_is_active` |
| `drive_file_deleted_permanently` | `drive.api.files.delete_entities` | per entity deleted | `entity_type` | capture inside loop |
| `drive_file_renamed` | `drive.api.files.rename` | after `drive_file.rename()` | `entity_type` | capture before `return` |
| `drive_file_moved` | `drive.api.files.move` | after each `doc.move()` | `cross_team: bool` | capture after loop |
| `drive_file_searched` | `drive.api.files.search` | after query runs | `results_count`, `query_length` | capture before `return result` |
| `drive_team_created` | `drive.api.product.create_team` | after team insert | `personal: bool` | capture after `team.save()` |
| `drive_user_invited` | `drive.api.product.invite_users` | after each new invite | `as_guest: bool`, `invite_count` | capture after loop |
| `drive_favourite_set` | `drive.api.files.set_favourite` | when favouriting (not clearing) | `entity_count` | capture when `entity["is_favourite"]` is True |

### Frontend

| Event name | Component | Trigger | Extra properties |
|------------|-----------|---------|-----------------|
| `drive_page_viewed` | `router.js` `afterEach` hook | every route change | `page_name` (route.name), `route` |
| `drive_file_previewed` | `File.vue` `onSuccess` callback | file loaded in preview | `file_type`, `mime_type` |
| `drive_share_dialog_opened` | `GenericPage.vue` actionItems share handler | share action clicked | `entity_type` (file/folder/document) |
| `drive_invite_sent` | `ShareDialog.vue` `addShares()` | Invite button clicked | `user_count`, `access_level` |
| `drive_link_copied` | `GenericPage.vue` copy-link action | Copy Link action clicked | `entity_type` |
| `drive_file_favourited` | `GenericPage.vue` favourite action | favourite action | `entity_type` |
| `drive_file_unfavourited` | `GenericPage.vue` unfavourite action | unfavourite action | `entity_type` |
| `drive_search_opened` | `SearchPopup.vue` | popup opened | — |
| `drive_view_toggled` | `DriveToolBar.vue` `viewState` watcher | grid/list toggle | `view` (grid/list) |
| `drive_file_moved` | `GenericPage.vue` `onDrop` handler | drag-and-drop file onto folder | `method: "drag_drop"` |
| `drive_sort_order_changed` | `DriveToolBar.vue` `sortOrder` watcher | user changes sort field or direction | `field`, `ascending` |
| `drive_link_auto_detected` | `GenericPage.vue` `newLink()` toast buttons | user accepts or dismisses the auto-detected link toast | `action` (accepted/dismissed) |
