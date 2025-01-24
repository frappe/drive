import { format } from "date-fns"
import { fromZonedTime } from "date-fns-tz"
import store from "../store"

export function formatSize(size, nDigits = 1) {
  if (size === 0) return "-"
  const k = 1000 // Change base to 1000 for decimal prefixes
  const digits = nDigits < 0 ? 0 : nDigits
  const sizes = [" B", " KB", " MB", " GB", " TB", " PB"] // Adjusted for decimal prefixes
  const i = Math.floor(Math.log(size) / Math.log(k))
  let decSize = parseFloat((size / Math.pow(k, i)).toFixed(digits)) + sizes[i]
  if (i === 0 || i === 1) {
    decSize = Math.round(size / Math.pow(k, i))
  } else {
    decSize = parseFloat((size / Math.pow(k, i)).toFixed(digits))
  }
  return decSize + sizes[i]
}

export function base2BlockSize(bytes, decimals = 2, current = 0) {
  if (bytes === 0) return "0 Bytes"

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))

  return (
    parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i + current]
  )
}

export function formatDate(date) {
  const serverTimeZone = store.state.serverTZ
  const dateObj = new Date(date)

  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const zonedDate = fromZonedTime(dateObj, serverTimeZone)
  const hourCycle = navigator.language || "en-US"

  const formattedDate = format(zonedDate, "MM/dd/yy", { timeZone })
  let formattedTime
  if (hourCycle === "en-US") {
    formattedTime = format(zonedDate, "hh:mm a", { timeZone })
  } else {
    formattedTime = format(zonedDate, "HH:mm", { timeZone })
  }
  return `${formattedDate}, ${formattedTime}`
}

export function formatMimeType(mimeType) {
  let icon = "unknown"
  if (!mimeType) return icon
  const generic = mimeType.split("/")[0]
  const specific = mimeType.split("/")[1]
  if (["image", "video", "audio"].includes(generic)) icon = generic
  else if (generic === "frappe_doc") icon = "Frappe Doc"
  else if (generic === "frappe_whiteboard") icon = "Frappe Whiteboard"
  else
    switch (specific) {
      case "pdf":
        icon = "pdf"
        break
      case "vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        icon = "spreadsheet"
        break
      case "vnd.openxmlformats-officedocument.presentationml.presentation":
        icon = "presentation"
        break
      case "vnd.openxmlformats-officedocument.wordprocessingml.document":
        icon = "word"
        break
      case "msword":
        icon = "word"
        break
      case "zip":
        icon = "zip"
        break
      case "x-tar":
        icon = "zip"
        break
      case "x-7z-compressed":
        icon = "zip"
        break
    }
  return icon
}

export function getDateDiffInDays(date1, date2) {
  const msPerDay = 1000 * 60 * 60 * 24
  const date1UTC = Date.UTC(
    date1.getFullYear(),
    date1.getMonth(),
    date1.getDate()
  )
  const date2UTC = Date.UTC(
    date2.getFullYear(),
    date2.getMonth(),
    date2.getDate()
  )
  return Math.floor((date1UTC - date2UTC) / msPerDay)
}
