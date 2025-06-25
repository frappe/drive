import { format } from "date-fns"
export function formatSize(size, nDigits = 1) {
  if (size === 0) return ""
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

export function base2BlockSize(bytes) {
  if (bytes === 0) return "0 bytes"
  const k = 1024
  const sizes = ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
  const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

export function formatDate(date) {
  if (!date) return ""
  const dateObj = new Date(date)
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone
  const hourCycle = navigator.language || "en-US"

  const formattedDate = format(dateObj, "MM/dd/yy", { timeZone })
  let formattedTime
  if (hourCycle === "en-US") {
    formattedTime = format(dateObj, "hh:mm a", { timeZone })
  } else {
    formattedTime = format(dateObj, "HH:mm", { timeZone })
  }
  return `${formattedDate}, ${formattedTime}`
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

export const formatPercent = (num) => {
  return new Intl.NumberFormat("default", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(num / 100)
}

export const COLOR_MAP = {
  Archive: "#C2A88D",
  Application: "#f472b6",
  Image: "#34BAE3",
  Video: "#E86C13",
  Audio: "#9C45E3",
  Document: "#0073CA",
  Spreadsheet: "#30A66D",
  Presentation: "#F5BA14",
  Text: "#E2E2E2",
  PDF: "#E03636",
  Book: "#E2E2E2",
  Unknown: "#3f3f46",
}
