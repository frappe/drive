import { Node, mergeAttributes } from "@tiptap/core"

export const InsNode = Node.create({
  name: "ins",
  inline: true,
  group: "inline*",
  parseHTML() {
    return [{ tag: "ins" }]
  },
  renderHTML({ HTMLAttributes }) {
    return ["ins", mergeAttributes(HTMLAttributes), 0]
  },
  addAttributes() {
    return {
      class: {
        default: null,
      },
    }
  },
})

export const DelNode = Node.create({
  name: "del",
  inline: true,
  group: "inline*",
  parseHTML() {
    return [{ tag: "del" }]
  },
  renderHTML({ HTMLAttributes }) {
    return ["del", mergeAttributes(HTMLAttributes), 0]
  },
  addAttributes() {
    return {
      class: {
        default: null,
      },
    }
  },
})
