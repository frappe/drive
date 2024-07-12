import { toast } from "../utils/toasts.js"

export async function getLink(entity) {
  const link = entity.is_group
    ? `${window.location.origin}/drive/folder/${entity.name}`
    : entity.document
    ? `${window.location.origin}/drive/document/${entity.name}`
    : `${window.location.origin}/drive/file/${entity.name}`

  try {
    await copyToClipboard(link)
    toast({
      title: "Copied link",
      position: "bottom-right",
      timeout: 2,
    })
  } catch (err) {
    if (err.name === "NotAllowedError") {
      toast({
        icon: "alert-triangle",
        iconClasses: "text-red-700",
        title: "Clipboard permission denied",
        position: "bottom-right",
      })
    } else {
      console.error("Failed to copy link:", err)
    }
  }
}

const copyToClipboard = (str) => {
  if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(str)
  } else {
    // Fallback to the legacy clipboard API
    const textArea = document.createElement("textarea")
    textArea.value = str
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand("copy")
    document.body.removeChild(textArea)
    return Promise.resolve()
  }
}
