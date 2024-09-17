import { Mark, mergeAttributes } from "@tiptap/core"
import { DiffType } from "./diffType"

export const DiffMarkExtension = Mark.create({
  name: "diffMark",

  addAttributes() {
    return {
      type: {
        renderHTML: ({ type }) => {
          const color = {
            [DiffType.Inserted]: "#bcf5bc",
            [DiffType.Deleted]: "#ff8989",
          }[type]
          return {
            style: "background-color: " + color,
          }
        },
      },
    }
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes),
      0,
    ]
  },
})
