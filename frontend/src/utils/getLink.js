import { toast } from "@/utils/toasts.js"
import router from "../router.js"

export function getLinkStem(entity) {
  return `${
    {
      true: "file",
      [new Boolean(entity.is_group)]: "folder",
      [new Boolean(entity.document)]: "document",
    }[true]
  }/${entity.name}`
}

export function getLink(entity, copy = true, withDomain = true) {
  const team = router.currentRoute.value.params.team
  let link = entity.is_link
    ? entity.path
    : `${
        withDomain ? window.location.origin + "/drive" : ""
      }/t/${team}/${getLinkStem(entity)}`

  if (!copy) return link
  try {
    copyToClipboard(link).then(() => toast(__("Copied link")))
  } catch (err) {
    if (err.name === "NotAllowedError") {
      toast({
        icon: "alert-triangle",
        iconClasses: "text-red-700",
        title: __("Clipboard permission denied"),
        position: "bottom-right",
      })
    } else {
      console.error(__("Failed to copy link:"), err)
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
