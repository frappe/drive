# Frappe Drive - Local Modifications

This document tracks custom modifications made to the Frappe Drive application.

## Collabora Online Integration (drive_wopi)

**Date:** December 2025
**Related App:** [drive_wopi](https://github.com/bvisible/drive_wopi)

### Modified Files

#### 1. `frontend/src/components/FileTypePreview/MSOfficePreview.vue`

**Purpose:** Modified to add Collabora Online editing option alongside the existing Microsoft Office viewer.

**Changes:**
- Added import for `CollaboraEditor` component
- Added choice dialog with 3 options: Edit (Collabora), View (Microsoft), Download
- Added `collaboraAvailable` check via `drive_wopi.wopi.discovery.check_collabora_status`
- Added `showCollaboraEditor` and `showMSViewer` state management

**Original behavior:** Showed a warning dialog then loaded MS Office Online viewer
**New behavior:** Shows a choice dialog with Edit/View/Download options

#### 2. `frontend/src/components/FileTypePreview/CollaboraEditor.vue` (NEW)

**Purpose:** New component to embed Collabora Online editor in an iframe.

**Features:**
- Hidden form to POST access_token to Collabora (required by WOPI protocol)
- Iframe to display Collabora editor
- PostMessage handling for save/close events from Collabora
- Loading state while fetching editor configuration

**API Dependencies:**
- `drive_wopi.wopi.discovery.get_editor_config` - Returns editor URL and access token

### Configuration Required

Add to `site_config.json`:

```json
{
    "collabora_server_url": "https://collabora.yourdomain.com",
    "collabora_jwt_secret": "your-secret-key-minimum-32-characters",
    "collabora_jwt_expiry_hours": 10
}
```

### Rebuild After Changes

After modifying these files, rebuild the frontend:

```bash
bench build --app drive
```

### Reverting Changes

To revert to original Drive behavior:

1. Remove `CollaboraEditor.vue`
2. Restore original `MSOfficePreview.vue` from git:
   ```bash
   cd apps/drive
   git checkout frontend/src/components/FileTypePreview/MSOfficePreview.vue
   ```
3. Rebuild: `bench build --app drive`
