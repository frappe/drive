import { toast } from "../utils/toasts.js"

export async function getLink(entity) {
  const link = entity.is_group
    ? `${window.location.origin}/drive/folder/${entity.name}`
    : entity.document
    ? `${window.location.origin}/drive/document/${entity.name}`
    : `${window.location.origin}/drive/file/${entity.name}`
  navigator.permissions.query({ name: "clipboard-write" }).then((result) => {
    if (result.state == "denied") {
      toast({
        icon: "alert-triangle",
        iconClasses: "text-red-700",
        title: "Clipboard permission denied",
        position: "bottom-right",
      })
    } else {
      copyToClipboard(link)
      toast({
        title: "Copied link",
        position: "bottom-right",
        timeout: 2,
      })
    }
  })
}

const copyToClipboard = (str) => {
  if (navigator && navigator.clipboard && navigator.clipboard.writeText)
    return navigator.clipboard.writeText(str)
  return Promise.reject("The Clipboard API is not available.")
}
