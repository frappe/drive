import { Node } from "@tiptap/core"
import { Plugin } from "@tiptap/pm/state"
import { getDocuments } from "@/resources/files"
import DocumentList from "../components/DocumentList.vue"
import tippy from "tippy.js"

import router from "@/router"
import { VueRenderer } from "@tiptap/vue-3"

const EmbedExtension = Node.create({
  name: "embed",
  addCommands() {
    return {
      embedDocument:
        (entity) =>
        ({ editor }) => {
          editor.commands.setIframe({
            src: `/drive/t/${entity.team}/document/${entity.name}/`,
            interactive: true,
          })

          const { state } = editor
          const from = component.props.range.from + 1
          const start = from - 2
          if (start < 0) return

          const tr = state.tr.delete(start, from)
          editor.view.dispatch(tr)
          closePopup()
        },
    }
  },
  addProseMirrorPlugins() {
    const editor = this.editor
    return [
      new Plugin({
        props: {
          handleTextInput(view, from, to, text) {
            const { state } = view
            const start = Math.max(0, from - 1)
            const existingText =
              state.doc.textBetween(start, from, "", "") + text

            if (existingText === "[[") {
              openEmbedSuggestion(view, from, editor)
            }
          },
          handleKeyDown(view, event) {
            if (!popup) return false

            if (event.key === "Escape" || event.key === "Backspace") {
              closePopup()
              return true
            }

            return false
          },
        },
      }),
    ]
  },
})

export default EmbedExtension
let popup, component
export function openEmbedSuggestion(view, from, editor) {
  const { team, entityName } = router.currentRoute.value.params
  if (!getDocuments.fetched) {
    getDocuments.fetch({ team })
  }
  component = new VueRenderer(DocumentList, {
    editor,
    props: {
      editor,
      range: { from, to: from },
      close,
      items: getDocuments.data
        .sort((a, b) => (a.modified > b.modified ? -1 : 1))
        .filter((k) => k.name !== entityName),
    },
  })

  // Create the tippy popup
  popup = tippy("body", {
    getReferenceClientRect: () => {
      const coords = view.coordsAtPos(from)
      return {
        top: coords.top,
        left: coords.left,
        width: 0,
        height: coords.bottom - coords.top,
      }
    },
    appendTo: () => document.body,
    content: component.element,
    showOnCreate: true,
    interactive: true,
    trigger: "manual",
    placement: "bottom-start",
  })
  popup[0].show()
}

// Cleanup function
function closePopup() {
  popup[0].destroy()
  component.destroy()
  component = null
  popup = null
}
