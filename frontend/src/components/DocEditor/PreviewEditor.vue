<template>
  <editor-content
    v-if="editor"
    :editor="editor"
  />
</template>

<script setup>
import {
  ref,
  onMounted,
  onBeforeUnmount,
  normalizeClass,
  inject,
  watch,
  computed,
} from "vue"
import { useStore } from "vuex"
import Link from "@tiptap/extension-link"
import TaskItem from "@tiptap/extension-task-item"
import TaskList from "@tiptap/extension-task-list"
import Typography from "@tiptap/extension-typography"
import StarterKit from "@tiptap/starter-kit"
import { Editor, EditorContent } from "@tiptap/vue-3"
import { IndexeddbPersistence } from "y-indexeddb"
import * as Y from "yjs"
import { Table } from "./extensions/table"
import { PageBreak } from "./extensions/Pagebreak"
import { Highlight } from "./extensions/backgroundColor"
import { CharacterCount } from "./extensions/character-count"
import { Collaboration } from "./extensions/collaboration"
import { Color } from "./extensions/color"
import { FontFamily } from "./extensions/font-family"
import { FontSize } from "./extensions/font-size"
import { Indent } from "./extensions/indent"
import { LineHeight } from "./extensions/lineHeight"
import { Placeholder } from "./extensions/placeholder"
import { TextAlign } from "./extensions/text-align"
import { TextStyle } from "./extensions/text-style"
import { Underline } from "./extensions/underline"
import { ResizableMedia } from "./extensions/resizenode"
import { generateDiffDocument } from "./genDiff"
import { DiffMarkExtension } from "./extensions/createDiffMark"
import { Annotation } from "./extensions/AnnotationExtension/annotation"

const editor = ref(null)
const document = ref(null)
const provider = ref(null)
const previewContent = ref()
const diffContent = ref()
const store = useStore()
const currentEditor = inject("editor")

const entity = computed(() => store.state.activeEntity)

const props = defineProps({
  yjsUpdate: {
    type: Uint8Array,
    required: true,
  },
  showChanges: {
    type: Boolean,
    default: false,
  },
})

onMounted(() => {
  const doc = new Y.Doc()
  Y.applyUpdate(doc, props.yjsUpdate)
  const indexeddbProvider = new IndexeddbPersistence("version-proxy-doc", doc)
  provider.value = indexeddbProvider
  document.value = doc
  provider.value.on("synced", () => {
    editor.value = new Editor({
      editable: false,
      // eslint-disable-next-line no-sparse-arrays
      extensions: [
        StarterKit.configure({
          history: false,
          heading: {
            levels: [1, 2, 3, 4, 5],
          },
          paragraph: {
            HTMLAttributes: {
              class: entity.value.version > 0 ? "not-prose" : "",
            },
          },
          listItem: {
            HTMLAttributes: {
              class: "prose-list-item",
            },
          },
          codeBlock: {
            HTMLAttributes: {
              spellcheck: false,
              class:
                "not-prose my-5 px-4 py-2 text-[0.9em] font-mono text-black bg-surface-menu-bar rounded border border-outline-gray-2 overflow-x-auto",
            },
          },
          blockquote: {
            HTMLAttributes: {
              class:
                "prose-quoteless text-black border-l-2 pl-2 border-outline-gray-3 text-[0.9em]",
            },
          },
          code: {
            HTMLAttributes: {
              class:
                "not-prose px-px font-mono bg-surface-menu-bar text-[0.85em] rounded-sm border border-outline-gray-2",
            },
          },
          bulletList: {
            keepMarks: true,
            keepAttributes: false,
            HTMLAttributes: {
              class: "",
            },
          },
          orderedList: {
            keepMarks: true,
            keepAttributes: false,
            HTMLAttributes: {
              class: "",
            },
          },
        }),
        Table,
        FontFamily.configure({
          types: ["textStyle"],
        }),
        TextAlign.configure({
          types: ["heading", "paragraph"],
          defaultAlignment: "left",
        }),
        ,
        PageBreak,
        Collaboration.configure({
          document: doc,
        }),
        LineHeight,
        Indent,
        Link.configure({
          openOnClick: false,
        }),
        Placeholder.configure({
          placeholder: "Press / for commands",
        }),
        Highlight.configure({
          multicolor: true,
        }),
        TaskList.configure({
          HTMLAttributes: {
            class: "not-prose",
          },
        }),
        TaskItem.configure({
          HTMLAttributes: {
            class: "my-task-item",
          },
        }),
        CharacterCount,
        Underline,
        Typography,
        TextStyle,
        FontSize.configure({
          types: ["textStyle"],
        }),
        Color.configure({
          types: ["textStyle"],
        }),
        ResizableMedia.configure({
          uploadFn: () => {},
        }),
        DiffMarkExtension,
        Annotation,
      ],
      editorProps: {
        attributes: {
          /* !p-0 to offset .Prosemirror */
          class: normalizeClass([
            `text-[14px] !p-0 mx-2 my-4 prose prose-sm prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-outline-gray-2 prose-th:border-outline-gray-2 prose-td:relative prose-th:relative prose-th:bg-surface-gray-2 rounded-b-lg max-w-[unset] pb-[50vh] md:px-[70px]`,
          ]),
        },
      },
    })
  })
})
watch(
  () => props.showChanges,
  (newValue) => {
    if (newValue) {
      if (diffContent.value) {
        editor.value.commands.setContent(diffContent.value.toJSON())
      } else {
        generateChanges()
      }
    } else {
      editor.value.commands.setContent(previewContent.value)
    }
  }
)

function generateChanges() {
  previewContent.value = editor.value.getJSON()
  diffContent.value = generateDiffDocument(
    editor.value.schema,
    currentEditor.value.view.state.doc.toJSON(),
    editor.value.view.state.doc.toJSON()
  )
  editor.value.commands.setContent(diffContent.value.toJSON())
}

onBeforeUnmount(() => {
  editor.value.destroy()
  provider.value.clearData()
  document.value.destroy()
})
</script>
