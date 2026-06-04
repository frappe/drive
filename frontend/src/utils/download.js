// Folder / multi-file downloads are streamed as a zip by the backend
// (drive.api.files.download_folder). Single files stream directly. Nothing is
// buffered in browser memory, so large folders no longer hang the tab.

export function entitiesDownload(entities, transfer = false) {
  // Single file → stream directly (supports transfer links).
  if (entities.length === 1 && !entities[0].is_group) {
    window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${
      entities[0].name
    }&trigger_download=1${transfer ? "&transfer=1" : ""}`
    return
  }

  // A folder, or a multi-selection → let the server build and stream the zip.
  const names = JSON.stringify(entities.map((entity) => entity.name))
  window.location.href = `/api/method/drive.api.files.download_folder?entities=${encodeURIComponent(
    names
  )}`
}
