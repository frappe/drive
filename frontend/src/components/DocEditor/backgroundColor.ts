import { Extension } from "@tiptap/core"
import "@tiptap/extension-text-style"

/* Default highlight extension creates a mark which is not compatible with `fontSize` */

export type HighlightOptions = {
  types: string[]
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    backgroundColor: {
      /**
       * Set the font size
       */
      toggleHighlight: (backgroundColor: string) => ReturnType
      /**
       * Unset the font size
       */
      unsetHighlight: () => ReturnType
    }
  }
}

export const Highlight = Extension.create<HighlightOptions>({
  name: "backgroundColor",

  addOptions() {
    return {
      types: ["textStyle"],
    }
  },

  addGlobalAttributes() {
    return [
      {
        types: this.options.types,
        attributes: {
          backgroundColor: {
            default: null,
            parseHTML: (element) =>
              element.style.backgroundColor.replace(/['"]+/g, ""),
            renderHTML: (attributes) => {
              if (!attributes.backgroundColor) {
                return {}
              }

              return {
                style: `background-color: ${attributes.backgroundColor}`,
              }
            },
          },
        },
      },
    ]
  },

  addCommands() {
    return {
      toggleHighlight:
        (backgroundColor) =>
        ({ chain }) => {
          return chain().setMark("textStyle", { backgroundColor }).run()
        },
      unsetHighlight:
        () =>
        ({ chain }) => {
          return chain()
            .setMark("textStyle", { backgroundColor: null })
            .removeEmptyTextStyle()
            .run()
        },
    }
  },
})
