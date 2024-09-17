import { Mark, mergeAttributes } from "@tiptap/core"

export const Ins = Mark.create({
  name: "ins",
  parseHTML() {
    return [
      {
        tag: "ins",
        priority: 600,
        getAttrs: (node) => {
          if (node.closest("code, table")) {
            return false
          }
          return true
        },
      },
    ]
  },
  renderHTML({ HTMLAttributes }) {
    return ["ins", mergeAttributes(HTMLAttributes), 0]
  },
})

export const Del = Mark.create({
  name: "del",
  parseHTML() {
    return [
      {
        tag: "del",
        priority: 600,
        getAttrs: (node) => {
          if (node.closest("code, table")) {
            return false
          }
          return true
        },
      },
    ]
  },
  renderHTML({ HTMLAttributes }) {
    return ["del", mergeAttributes(HTMLAttributes), 0]
  },
})
