import { Node } from "@tiptap/core"
import { Plugin } from "@tiptap/pm/state"
import { getDocuments } from "@/resources/files"
import DocumentList from "../components/DocumentList.vue"
import tippy from "tippy.js"

import { watch, ref, computed } from "vue"
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
              triggerPosition = start
              openEmbedSuggestion(view, from, editor)
            }
            if (popup && component && text != "[") {
              search.value =
                state.doc.textBetween(triggerPosition + 2, to, "", "") + text
              //       search = query
              //           console.log(text)
              // search = search + text

              // const { team, entityName } = router.currentRoute.value.params
              // getDocuments.fetch({ team, only_parent: 0, search })

              // component.updateProps({
              //   items: getDocuments.data
              //     .sort((a, b) => (a.modified > b.modified ? -1 : 1))
              //     .filter((k) => k.name !== entityName && k.name.includes(search))
              // })

              return false
            }
          },
          handleKeyDown(view, event) {
            if (!popup) return false
            const inPopup = popup && component && search.value
            if (component) {
              const val = component.ref.onKeyDown({ event })
              if (val) return val
            }
            if (
              event.key === "Escape" ||
              (event.key === "Backspace" && !inPopup)
            ) {
              closePopup()
              return true
            }
            if (event.key === "Backspace" && inPopup) {
              search.value = search.value.slice(0, -1)
            }

            return false
          },
        },
      }),
    ]
  },
})

export default EmbedExtension
let popup, component, triggerPosition
const search = ref(null)
const items = computed(() =>
  getDocuments.data
    .sort((a, b) => (a.modified > b.modified ? -1 : 1))
    .filter((k) => k.name !== router.currentRoute.value.params.entityName)
)
export async function openEmbedSuggestion(view, from, editor) {
  const { team, entityName } = router.currentRoute.value.params
  component = new VueRenderer(DocumentList, {
    editor,
    props: {
      editor,
      range: { from, to: from },
      close,
      items: items.value,
      loading: true,
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
  search.value = ""
}

// Cleanup function
function closePopup() {
  popup[0].destroy()
  component.destroy()
  component = null
  popup = null
}

watch(search, async (val) => {
  getDocuments.fetch(
    {
      team: router.currentRoute.value.params.team,
      only_parent: 0,
      search: search.value,
    },
    {
      onSuccess: () => {
        component &&
          component.updateProps({
            items: items.value,
          })
      },
    }
  )
})
