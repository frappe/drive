<template>
  <div class="flex w-full h-100 overflow-y-hidden">
    <div class="flex-1 md:w-auto md:p-0">
      <div
        v-if="current"
        class="bg-surface-blue-2 text-ink-gray-8 p-3 text-base flex justify-between items-center"
      >
        <div class="flex flex-col gap-1">
          <div>
            This is a snapshot of this document from
            {{ formatDate(current.title) }}.
          </div>
          <div class="text-xs text-ink-gray-7">
            Editing is disabled until you exit this preview.
          </div>
        </div>
        <div class="flex gap-2">
          <Button
            variant="ghost"
            label="Exit"
            @click="emitter.emit('clear-snapshot')"
            class="hover:!bg-surface-blue-2 hover:underline"
          />
          <Button
            variant="solid"
            @click="emitter.emit('restore-snapshot')"
            label="Restore"
          />
        </div>
      </div>
      <div
        @click="
          $event.target.tagName === 'DIV' &&
            textEditor.editor?.chain?.().focus?.().run?.()
        "
        class="mx-auto cursor-text w-full flex justify-center h-full"
      >
        <div
          v-if="!updated"
          class="text-center h-full flex justify-center items-center text-sm font-semibold"
        >
          Updating...
        </div>
        <FTextEditor
          v-if="
            !collab ||
            editorExtensions.find((k) => k.name === 'collaborationCursor')
          "
          ref="textEditor"
          class="min-w-full h-full flex flex-col"
          :style="{ fontFamily: `var(--font-${settings?.font_family})` }"
          :editor-class="[
            'prose-sm min-h-[4rem] !min-w-0 mx-auto',
            `text-[${settings?.font_size || 15}px]`,
            `leading-[${settings?.line_height || 1.5}]`,
            settings?.custom_css,
            current ? 'pb-24' : '',
          ]"
          :content="!collab ? rawContent : undefined"
          :editable
          :upload-function="
            (file) => {
              const fileUpload = useFileUpload()
              return fileUpload.upload(file, {
                private: entity.is_private,
                folder: entity.name,
                upload_endpoint: `/api/method/drive.api.files.upload_embed`,
              })
            }
          "
          @change="
            (val) => {
              if (val === rawContent || current) return
              rawContent = val
              if (collab) yjsContent = Y.encodeStateAsUpdate(doc)
              if (db)
                db.transaction(['content'], 'readwrite')
                  .objectStore('content')
                  .put({ val, saved: new Date() }, props.entity.name)
              edited = true
              autosave()
              autoversion()
            }
          "
          :mentions="users"
          placeholder="Start writing here..."
          :bubble-menu="bubbleMenuButtons"
          :extensions="editorExtensions"
        >
          <template #top>
            <TextEditorFixedMenu
              v-if="editable"
              class="w-full overflow-x-auto border-b border-outline-gray-modals justify-center py-1.5"
              :buttons="bubbleMenuButtons"
            />
          </template>
          <template #editor="{ editor }">
            <EditorContent
              :editor="editor"
              class="h-full overflow-y-auto"
            />
          </template>
        </FTextEditor>
      </div>
    </div>
    <FloatingComments
      v-if="comments.length"
      :entity="entity"
      :editor
      v-model:show-comments="showComments"
      v-model:active-comment="activeComment"
      v-model:comments="comments"
    />
  </div>
</template>

<script setup>
import { toast } from "@/utils/toasts.js"
import {
  TextEditor as FTextEditor,
  TextEditorFixedMenu,
  debounce,
  useFileUpload,
  useDoc,
} from "frappe-ui"
import { v4 as uuidv4 } from "uuid"
import {
  computed,
  defineAsyncComponent,
  onMounted,
  ref,
  onBeforeUnmount,
  h,
  watch,
  getCurrentInstance,
} from "vue"
import store from "@/store"
import { EditorContent } from "@tiptap/vue-3"
import FontFamily from "./extensions/font-family"
import FloatingQuoteButton from "./extensions/comment"
import { CharacterCount } from "./extensions/character-count"
import { CollaborationCursor } from "./extensions/collaboration-cursor"
import CommentExtension from "@sereneinserenade/tiptap-comment-extension"
import FloatingComments from "./components/FloatingComments.vue"
import { printDoc, getRandomColor } from "@/utils/files"
import { rename } from "@/resources/files"
import { onKeyDown } from "@vueuse/core"
import emitter from "@/emitter"
import Collaboration from "@tiptap/extension-collaboration"
import * as Y from "yjs"
import { IndexeddbPersistence } from "y-indexeddb"
import { ySyncPluginKey } from "y-prosemirror"
import { WebrtcProvider } from "y-webrtc"

import H1 from "./icons/h-1.vue"
import H2 from "./icons/h-2.vue"
import H3 from "./icons/h-3.vue"

import LucideMessageCircle from "~icons/lucide/message-circle"
import { formatDate } from "../../utils/format"

const textEditor = ref("textEditor")
const updated = ref(true)
const current = defineModel("current")
const editor = computed(() => {
  let editor = textEditor.value?.editor
  return editor
})
const editable = computed(() => !!props.entity.write && !props.settings?.lock)
defineExpose({ editor })

const rawContent = defineModel("rawContent")
const yjsContent = defineModel("yjsContent")
const showComments = defineModel("showComments")
const edited = defineModel("edited")

const props = defineProps({
  entity: Object,
  settings: Object,
  showResolved: Boolean,
  users: Object,
  currentVersion: { required: false, type: Object },
})
const comments = ref([])
const settings = computed(() => {
  for (let [k, v] in Object.entries(props.settings)) {
    if (v === "global") delete props.settings[k]
  }
  return {
    ...writerSettings.doc?.settings,
    ...props.settings,
  }
})

const emit = defineEmits(["newVersion", "saveDocument"])
const activeComment = ref(null)
const autosave = debounce(() => emit("saveDocument"), 2000)
const autoversion = debounce(() => {
  if (!collab.value) return
  const snap = Y.encodeSnapshot(Y.snapshot(doc))
  emit("newVersion", snap)
}, 1000)

watch(
  () => props.currentVersion,
  (val) => {
    if (!val) return
    toast("Changing version")
    const { view } = editor.value
    view.dispatch(
      view.state.tr.setMeta(ySyncPluginKey, {
        snapshot: Y.decodeSnapshot(val[1].snapshot),
        prevSnapshot: Y.decodeSnapshot(val[0].snapshot),
      })
    )
  }
)

const writerSettings = useDoc({
  doctype: "Drive Settings",
  name: store.state.user.id,
  immediate: true,
  transform: (doc) => {
    doc.settings = JSON.parse(doc.writer_settings)
    return doc
  },
})
writerSettings.onSuccess(({ font_family }) => {
  if (!rawContent.value)
    editor.value
      .chain()
      .focus()
      .setFontFamily(`var(--font-${font_family})`)
      .run()
})

const createNewComment = (editor) => {
  showComments.value = true
  const id = uuidv4()
  editor.chain().focus().setComment(id).run()
  const orderedComments = getOrderedComments(editor.state.doc)
  const newComment = {
    name: id,
    owner: store.state.user.id,
    creation: new Date(),
    content: "",
    edit: true,
    new: true,
    loading: true,
    replies: [],
  }
  comments.value = [...comments.value, newComment].toSorted((a, b) => {
    const pos1 = orderedComments.findIndex((k) => k.id === a.name)
    const pos2 = orderedComments.findIndex((k) => k.id === b.name)
    return pos1 - pos2
  })
  activeComment.value = id
  emit("saveDocument")
}

const ExtendedCommentExtension = CommentExtension.extend({
  addAttributes() {
    return {
      ...this.parent?.(),

      resolved: {
        default: false,
        parseHTML: (el) => el.hasAttribute("data-resolved"),
        renderHTML: (attrs) =>
          attrs.resolved ? { "data-resolved": "true" } : {},
      },
    }
  },
  addCommands() {
    return {
      ...this.parent?.(),

      resolveComment:
        (commentId, resolved = true) =>
        ({ state, tr, dispatch }) => {
          const { doc } = state
          const markType = state.schema.marks[this.name]

          doc.descendants((node, pos) => {
            if (!node.isText) return true
            node.marks.forEach((mark) => {
              if (
                mark.type === markType &&
                mark.attrs.commentId === commentId
              ) {
                const updatedMark = markType.create({
                  ...mark.attrs,
                  resolved,
                })

                tr.removeMark(pos, pos + node.nodeSize, markType)
                tr.addMark(pos, pos + node.nodeSize, updatedMark)
              }
            })
          })

          if (tr.docChanged && dispatch) {
            dispatch(tr)
            return true
          }

          return false
        },
    }
  },
})

const editorExtensions = [
  CharacterCount,
  FontFamily.configure({
    types: ["textStyle"],
  }),
  FloatingQuoteButton.configure({
    onClick: () => {
      createNewComment(editor.value)
    },
  }),
  ExtendedCommentExtension.configure({
    onCommentActivated: (id) => {
      let isResolved = comments.value.find((k) => id === k.name)?.resolved
      if (id && (!isResolved || showResolved)) {
        activeComment.value = id
        showComments.value = true
        document.querySelector(`span[data-comment-id="${id}"]`).scrollIntoView({
          behavior: "smooth",
          block: "start",
          inline: "nearest",
        })
      }
    },
  }),
]

let prov, doc
const collab = computed(() => props.settings.collab)
if (collab.value) {
  doc = new Y.Doc({ gc: false })

  const permanentUserData = new Y.PermanentUserData(doc)
  permanentUserData.setUserMapping(doc, doc.clientID, "Administrator")
  const colors = [
    { light: "#ecd44433", dark: "#ecd444" },
    { light: "#ee635233", dark: "#ee6352" },
    { light: "#6eeb8333", dark: "#6eeb83" },
  ]
  new IndexeddbPersistence("fdoc-" + props.entity.name, doc)
  if (yjsContent.value) Y.applyUpdate(doc, yjsContent.value)
  prov = new WebrtcProvider("fdoc-" + props.entity.name, doc, {
    signaling: ["wss://signal.frappe.cloud"],
  })

  editorExtensions.push(
    Collaboration.configure({
      document: doc,
      field: "default",
      ySyncOptions: {
        permanentUserData,
        colors,
      },
    }),
    CollaborationCursor.configure({
      provider: prov,
      user: {
        name: store.state.user.fullName,
        avatar: store.state.user.imageURL,
        color: getRandomColor(),
      },
    })
  )
}

const CommentAction = {
  label: "Comment",
  icon: LucideMessageCircle,
  action: createNewComment,
  isActive: () => false,
}

const bubbleMenuButtons = [
  "Paragraph",
  [
    {
      text: "H1",
      icon: H1,
      action: (editor) =>
        editor.chain().focus().toggleHeading({ level: 1 }).run(),
      isActive: (editor) => editor.isActive("heading", { level: 1 }),
    },
    {
      text: "H2",
      icon: H2,
      action: (editor) =>
        editor.chain().focus().toggleHeading({ level: 2 }).run(),
      isActive: (editor) => editor.isActive("heading", { level: 2 }),
    },
    {
      text: "H3",
      icon: H3,
      action: (editor) =>
        editor.chain().focus().toggleHeading({ level: 3 }).run(),
      isActive: (editor) => editor.isActive("heading", { level: 3 }),
    },
  ],
  "Separator",
  "Bold",
  "Italic",
  "Link",
  "Strikethrough",
  "Separator",
  {
    label: "Inter",
    class: "font-inter",
    component: h(
      defineAsyncComponent(() => import("./components/FontFamily.vue")),
      { editor }
    ),
  },
  "FontColor",
  "Separator",
  ["Bullet List", "Numbered List", "Task List"],
  "Separator",
  ["Align Left", "Align Center", "Align Right"],
  "Separator",
  CommentAction,
  "Image",
  "Video",
  "Blockquote",
  "Code",
  [
    "InsertTable",
    "AddColumnBefore",
    "AddColumnAfter",
    "DeleteColumn",
    "AddRowBefore",
    "AddRowAfter",
    "DeleteRow",
    "MergeCells",
    "SplitCell",
    "ToggleHeaderColumn",
    "ToggleHeaderRow",
    "ToggleHeaderCell",
    "DeleteTable",
  ],
]

emitter.on("printFile", () => {
  if (editor.value) printDoc(editor.value.getHTML())
})
const component = getCurrentInstance()

onMounted(() => {
  if (props.entity.mime_type === "frappe_doc") {
    const orderedComments = getOrderedComments(editor.value.state.doc)
    comments.value = props.entity.comments.toSorted((a, b) => {
      const pos1 = orderedComments.findIndex((k) => k.id === a.name)
      const pos2 = orderedComments.findIndex((k) => k.id === b.name)
      return pos1 - pos2
    })
  }
  if (collab.value) {
    if (component.vnode.key > 0) updated.value = false
  }
})

onBeforeUnmount(() => {
  comments.value
    .filter((k) => k.new)
    .filter(({ name }) => editor.value.commands.unsetComment(name))
  if (prov) {
    prov.disconnect()
    prov.destroy()
  }
})

onKeyDown("Enter", evalImplicitTitle)
onKeyDown("s", (e) => {
  if (!e.metaKey || !e.shiftKey) {
    return
  }
  e.preventDefault()
  emit("saveDocument")
  toast({
    title: "Saving document",
  })
})

function getOrderedComments(doc) {
  const comments = []
  doc.descendants((node, pos) => {
    node.marks.forEach((mark) => {
      if (mark.type.name === "comment" && mark.attrs.commentId) {
        comments.push({ id: mark.attrs.commentId, pos })
      }
    })
  })

  return comments.sort((a, b) => a.pos - b.pos)
}

// Local saving
const db = ref()
watch(db, (db) => {
  if (!props.entity.write || collab.value) return
  db
    .transaction(["content"])
    .objectStore("content")
    .get(props.entity.name).onsuccess = (val) => {
    // Hack until we get versioning.
    if (
      val.target.result?.val?.length > 20 &&
      val.target.result.saved > new Date(props.entity.modified)
    )
      rawContent.value = val.target.result.val
  }
})
if (props.entity.write) {
  const request = window.indexedDB.open("Writer", 1)
  request.onsuccess = (event) => {
    db.value = event.target.result
  }
  request.onupgradeneeded = () => {
    if (!request.result.objectStoreNames.contains("content"))
      request.result.createObjectStore("content")
  }
}

function evalImplicitTitle() {
  if (!props.entity.title.startsWith("Untitled Document")) return
  const implicitTitle = editor.value.state.doc.firstChild.textContent
    .replaceAll("#", "")
    .replaceAll("@", "")
    .trim()
  if (implicitTitle.length === 0) return

  if (implicitTitle.length) {
    rename.submit({
      entity_name: props.entity.name,
      new_title: implicitTitle,
    })
  }
}
</script>

<style>
@import url("./editor.css");
</style>
