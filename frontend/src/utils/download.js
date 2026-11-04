import JSZip from "jszip"
import { ref } from "vue"
import { toast } from "./toasts"
import { printDoc } from "./files"
import emitter from "@/emitter"
import router from "@/router"

// Renders a Drive-themed error toast. Prefers the frappe exception message
// (error.messages[0]) and falls back to a friendly message for network /
// system / server failures so users never see a silent or cryptic error.
function showDownloadError(error, fallback) {
  let message = fallback
  const raw = error?.message || error?.messages?.join(" ") || ""
  if (error?.messages?.length) {
    message = error.messages[0]
  } else if (raw) {
    message = raw
  }
  if (error?.status >= 500 || /^5\d\d\b|internal server|service unavailable/i.test(raw)) {
    message = "Something went wrong on the server. Please try again later."
  } else if (error?.status >= 400 || /^4\d\d\b/i.test(raw)) {
    message = "That file isn't available anymore. It may have been moved or deleted."
  } else if (/failed to fetch|networkerror|load failed|offline|aborted/i.test(raw)) {
    message = "You're offline. Check your internet connection and try again."
  }
  console.error("[Drive][Download] error:", error)
  toast({ title: message, type: "error" })
}

// Prevents starting a second download while one is already in progress.
// Set synchronously (before any async work) so rapid double-clicks cannot
// race and both begin; cleared in a finally on every download path.
// Exported as a reactive ref so the UI can render a spinner / disable the
// download button while a download is running.
export const downloadInProgress = ref(false)
function isDownloadInProgress() {
  if (downloadInProgress.value) {
    toast({
      title: "A download is already in progress. Please wait...",
      type: "info",
    })
    return true
  }
  downloadInProgress.value = true
  return false
}
function clearDownloadInProgress() {
  downloadInProgress.value = false
}

export function entitiesDownload(team, entities, transfer = false) {
  if (isDownloadInProgress()) return
  if (entities.length === 1) {
    if (entities[0].mime_type === "frappe_doc") {
      if (router.currentRoute.value.name === "Document") {
        emitter.emit("printFile")
        clearDownloadInProgress()
        return
      }
      return fetch(
        `/api/method/drive.api.files.get_file_content?entity_name=${entities[0].name}`
      )
        .then(async (data) => {
          const raw_html = (await data.json()).message
          printDoc(raw_html)
        })
        .catch((error) => {
          clearDownloadInProgress()
          showDownloadError(
            error,
            "Couldn't download this document. Please try again."
          )
        })
        .finally(() => clearDownloadInProgress())
    }
    if (entities[0].is_group) {
      return folderDownload(team, entities[0])
    }
    if (entities[0].is_link) {
      clearDownloadInProgress()
      toast({
        title: `"${entities[0].title}" is a link and can't be downloaded directly.`,
        type: "info",
      })
      return
    }
    const t = toast(`Downloading "${entities[0].title}"...`)
    const url = `/api/method/drive.api.files.get_file_content?entity_name=${
      entities[0].name
    }&trigger_download=1${transfer ? "&transfer=1" : ""}`
    return fetch(url)
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => null)
          throw Object.assign(
            new Error(
              body?.messages?.[0] ||
                `Failed to download "${entities[0].title}" (${response.status})`
            ),
            { status: response.status }
          )
        }
        return response.blob()
      })
      .then((blob) => {
        const downloadLink = document.createElement("a")
        downloadLink.href = URL.createObjectURL(blob)
        downloadLink.download = entities[0].title
        document.body.appendChild(downloadLink)
        downloadLink.click()
        document.body.removeChild(downloadLink)
        document.getElementById(t)?.remove()
        clearDownloadInProgress()
      })
      .catch((error) => {
        document.getElementById(t)?.remove()
        clearDownloadInProgress()
        showDownloadError(
          error,
          `Couldn't download "${entities[0].title}". Please try again.`
        )
      })
  }

  return decideDownload(team, entities, "Drive Download " + new Date().getTime())
}

export function folderDownload(team, root_entity) {
  return decideDownload(team, [root_entity], root_entity.title)
}

// Client-side zipping is fast but buffers every file in browser memory, so it's
// only safe for small selections. Heavy ones go through the server-side
// enqueue flow (drive.api.download.*) instead. `estimate_download` is a cheap
// DB-only size/count walk that decides which path to take.
const CLIENT_ZIP_MAX_BYTES = 100 * 1024 * 1024 // 100 MB
const CLIENT_ZIP_MAX_FILES = 2000

function decideDownload(team, entities, filename) {
  const names = entities.map((e) => e.name)
  return fetch("/api/method/drive.api.download.estimate_download", {
    method: "POST",
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ team, entity_names: names }),
  })
    .then(async (response) => {
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw Object.assign(
          new Error(
            body?.messages?.[0] || `Failed to estimate download (${response.status})`
          ),
          { status: response.status }
        )
      }
      return response.json()
    })
    .then(({ message }) => {
      if (
        message.total_size <= CLIENT_ZIP_MAX_BYTES &&
        message.count <= CLIENT_ZIP_MAX_FILES
      ) {
        return clientZipDownload(team, entities, filename)
      }
      return serverZipDownload(team, names, filename)
    })
    .catch((error) => {
      clearDownloadInProgress()
      showDownloadError(
        error,
        "Couldn't download the selected files. Please try again."
      )
    })
}

const POLL_INTERVAL_MS = 2000
// Keep polling as long as the server job is still running. The enqueued job has
// a 30-minute timeout; give it nearly that long here before giving up. Real
// builds finish in seconds now (media is STOREd, not re-compressed), so this
// ceiling only matters if a job is genuinely stuck.
const POLL_TIMEOUT_MS = 25 * 60 * 1000

// Small-selection path: build the zip in the browser with JSZip (fast, no
// queue latency). Docs become .html (no server-side PDF), links are skipped.
function clientZipDownload(team, entities, filename) {
  const t = toast("Preparing download...")
  const zip = new JSZip()

  const processEntity = async (entity, parentFolder) => {
    if (entity.is_link) return
    if (entity.is_group) {
      const folder = parentFolder.folder(entity.title)
      const children = await get_children(team, entity.name)
      for (const child of children) {
        await processEntity(child, folder)
      }
      return
    }
    if (entity.document || entity.mime_type === "frappe_doc") {
      const content = await get_doc_content(entity)
      parentFolder.file(entity.title + ".html", content)
      return
    }
    const fileContent = await get_file_content(entity)
    parentFolder.file(entity.title, fileContent)
  }

  const processAll = async () => {
    for (const entity of entities) {
      await processEntity(entity, zip)
    }
  }

  return processAll()
    .then(() => zip.generateAsync({ type: "blob", streamFiles: true }))
    .then((content) => {
      const downloadLink = document.createElement("a")
      downloadLink.href = URL.createObjectURL(content)
      downloadLink.download = filename + ".zip"
      document.body.appendChild(downloadLink)
      downloadLink.click()
      document.body.removeChild(downloadLink)
      document.getElementById(t)?.remove()
      clearDownloadInProgress()
    })
    .catch((error) => {
      document.getElementById(t)?.remove()
      clearDownloadInProgress()
      showDownloadError(
        error,
        "Couldn't download the selected files. Please try again."
      )
    })
}

function get_doc_content(entity) {
  return fetch(
    `/api/method/drive.api.download.get_doc_content?entity_name=${entity.name}`
  )
    .then(async (response) => {
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw Object.assign(
          new Error(
            body?.messages?.[0] || `Failed to fetch doc content (${response.status})`
          ),
          { status: response.status }
        )
      }
      return (await response.json()).message || ""
    })
}

function get_file_content(entity) {
  const fileUrl =
    entity.src ||
    "/api/method/" +
      `drive.api.files.get_file_content?entity_name=${entity.name}&trigger_download=1`
  return fetch(fileUrl).then(async (response) => {
    if (response.ok) {
      return response.blob()
    } else if (response.status === 204) {
      return new Blob()
    } else {
      const body = await response.json().catch(() => null)
      throw Object.assign(
        new Error(
          body?.messages?.[0] ||
            `Failed to fetch "${entity.title}" (${response.status})`
        ),
        { status: response.status }
      )
    }
  })
}

function get_children(team, entity_name) {
  const url =
    "/api/method/" +
    `drive.api.list.files?team=${team}&entity_name=${entity_name}&limit=5000`
  return fetch(url, {
    method: "GET",
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  })
    .then(async (response) => {
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw Object.assign(
          new Error(
            body?.messages?.[0] || `Failed to list files (${response.status})`
          ),
          { status: response.status }
        )
      }
      return response.json()
    })
    .then((json) => json.message)
}

// Builds the zip on the server (frappe.enqueue), polls until it's ready, then
// streams the finished zip to the browser. Keeps heavy zipping off the browser
// so large folders don't exhaust tab memory (RangeError) or trip fetch timeouts.
function serverZipDownload(team, entity_names, filename) {
  const t = toast("Preparing download...")
  const progressEl = document.createElement("div")
  progressEl.id = "drive-download-progress"
  progressEl.style.cssText =
    "position:fixed;top:1rem;left:50%;transform:translateX(-50%);" +
    "z-index:9999;background:#1c1c1c;color:#fff;padding:.5rem 1rem;" +
    "border-radius:.5rem;font-size:.875rem;box-shadow:0 2px 12px rgba(0,0,0,.35)"
  document.body.appendChild(progressEl)

  const removeProgress = () => {
    document.getElementById("drive-download-progress")?.remove()
  }

  return fetch("/api/method/drive.api.download.download_zip", {
    method: "POST",
    headers: {
      "X-Frappe-CSRF-Token": window.csrf_token,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ team, entity_names, filename }),
  })
    .then(async (response) => {
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw Object.assign(
          new Error(
            body?.messages?.[0] || `Failed to start download (${response.status})`
          ),
          { status: response.status }
        )
      }
      return response.json()
    })
    .then(({ message }) => message.download_id)
    .then((download_id) =>
      pollDownloadStatus(download_id, (processed, total) => {
        progressEl.textContent = `Zipping ${processed}/${total}…`
      })
    )
    .then((download_id) => {
      const url =
        `/api/method/drive.api.download.get_download_zip` +
        `?download_id=${download_id}`
      const downloadLink = document.createElement("a")
      downloadLink.href = url
      downloadLink.download = ""
      document.body.appendChild(downloadLink)
      downloadLink.click()
      document.body.removeChild(downloadLink)
      document.getElementById(t)?.remove()
      removeProgress()
      clearDownloadInProgress()
    })
    .catch((error) => {
      document.getElementById(t)?.remove()
      removeProgress()
      clearDownloadInProgress()
      showDownloadError(
        error,
        "Couldn't download the selected files. Please try again."
      )
    })
}

function pollDownloadStatus(download_id, onProgress) {
  return new Promise((resolve, reject) => {
    const startedAt = Date.now()
    let retries = 0
    const poll = () => {
      fetch(
        `/api/method/drive.api.download.download_status?download_id=${download_id}`
      )
        .then((response) => response.json())
        .then(({ message }) => {
          retries = 0
          if (message.status === "ready") {
            resolve(download_id)
          } else if (message.status === "error") {
            reject(
              Object.assign(
                new Error(message.message || "Download failed on the server."),
                { status: 500 }
              )
            )
          } else if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
            reject(
              Object.assign(
                new Error(
                  "Download is still being prepared on the server. Please try again in a few minutes."
                )
                // no `status` here so showDownloadError keeps this friendly message
              )
            )
          } else {
            if (onProgress && message.total) {
              onProgress(message.processed || 0, message.total)
            }
            setTimeout(poll, POLL_INTERVAL_MS)
          }
        })
        .catch((error) => {
          if (retries < 3 && Date.now() - startedAt < POLL_TIMEOUT_MS) {
            retries++
            setTimeout(poll, POLL_INTERVAL_MS)
          } else {
            reject(error)
          }
        })
    }
    poll()
  })
}
