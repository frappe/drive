import {
  AlignLeft,
  AlignRight,
  AlignCenter,
  AlignHorizontalJustifyStart,
  AlignHorizontalJustifyEnd,
  Trash,
} from "lucide-vue-next"
import { Component } from "vue"
interface ResizableMediaAction {
  tooltip: string
  icon: Component

  action?: (updateAttributes: (o: Record<string, any>) => any) => void
  isActive?: (attrs: Record<string, any>) => boolean
  delete?: (d: () => void) => void
}

export const resizableMediaActions: ResizableMediaAction[] = [
  {
    tooltip: "Align left",
    action: (updateAttributes) =>
      updateAttributes({
        dataAlign: "left",
        dataFloat: null,
      }),
    icon: AlignLeft,
    isActive: (attrs) => attrs.dataAlign === "left",
  },
  {
    tooltip: "Align center",
    action: (updateAttributes) =>
      updateAttributes({
        dataAlign: "center",
        dataFloat: null,
      }),
    icon: AlignCenter,
    isActive: (attrs) => attrs.dataAlign === "center",
  },
  {
    tooltip: "Align right",
    action: (updateAttributes) =>
      updateAttributes({
        dataAlign: "right",
        dataFloat: null,
      }),
    icon: AlignRight,
    isActive: (attrs) => attrs.dataAlign === "right",
  },
  {
    tooltip: "Float left",
    action: (updateAttributes) =>
      updateAttributes({
        dataAlign: null,
        dataFloat: "left",
      }),
    icon: AlignHorizontalJustifyStart,
    isActive: (attrs) => attrs.dataFloat === "left",
  },
  {
    tooltip: "Float right",
    action: (updateAttributes) =>
      updateAttributes({
        dataAlign: null,
        dataFloat: "right",
      }),
    icon: AlignHorizontalJustifyEnd,
    isActive: (attrs) => attrs.dataFloat === "right",
  },
  {
    tooltip: "Delete",
    icon: Trash,
    delete: (deleteNode) => deleteNode(),
  },
]
