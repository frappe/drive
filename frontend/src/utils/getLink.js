import { toast } from "@/utils/toasts.js"
import router from "../router.js"
import { scrubTitle } from "@/utils/helpers.ts"

import { scrubTitle } from "@/utils/helpers"

export function getLinkStem(entity) {
  const scrubbedSlug = scrubTitle(entity.name)
  const id = entity.id || entity.uuid || entity.name // fallback
  return `${
    {
      true: "file",
      [new Boolean(entity.is_group)]: "folder",
      [new Boolean(entity.document)]: "document",
    }[true]
  }/${id}-${scrubbedSlug}`
}


export function getLink(entity, copy = true) {
  const team = router.currentRoute.value.params.team
  let link = entity.is_link
    ? entity.path
    : `${window.location.origin}/drive/t/${team}/${getLinkStem(entity)}`

  if (!copy) return link
  try {
    copyToClipboard(link).then(() => toast("Copied link"))
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
