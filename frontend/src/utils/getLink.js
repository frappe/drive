import { toast } from "@/utils/toasts.js"
import router from "../router.js"

export async function getLink(entity) {
  const team = router.currentRoute.value.params.team
  const link = entity.is_group
    ? `${window.location.origin}/drive/${team}/folder/${entity.name}`
    : entity.document
    ? `${window.location.origin}/drive/${team}/document/${entity.name}`
    : `${window.location.origin}/drive/${team}/file/${entity.name}`

  try {
    await copyToClipboard(link)
    toast("Copied link")
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
