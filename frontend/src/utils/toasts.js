import { toast as fToast } from "frappe-ui"
import { h } from "vue"

const toast = (obj) => {
  if (typeof obj === "string") return fToast.success(obj)
  const { title, text, buttons, icon, duration } = obj
  fToast.success(title, {
    action: buttons?.[0],
    icon: icon && h(icon, { class: "text-ink-white" }),
    duration: duration || 5,
  })
}
export { toast }
