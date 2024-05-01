import { mergeAttributes, Node } from "@tiptap/core"

export interface DetailContentOptions {
  readonly HTMLAttributes: Record<string, unknown>
}

export const DetailsContent = Node.create<DetailContentOptions>({
  name: `detailsContent`,

  content: `block+`,

  group: `block`,

  allowGapCursor: true,

  parseHTML() {
    return [
      {
        tag: `div[data-type="details-content"]`,
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      `div`,
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        "data-type": `details-content`,
      }),
      0,
    ]
  },
})
