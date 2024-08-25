import { mergeAttributes, Node } from "@tiptap/core"

export interface SummaryOptions {
  readonly HTMLAttributes: Record<string, unknown>
}

export const DetailsSummary = Node.create<SummaryOptions>({
  name: `summary`,

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  content: `paragraph`,

  group: `block`,

  parseHTML() {
    return [
      {
        tag: `summary`,
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      `summary`,
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes),
      0,
    ]
  },
})
