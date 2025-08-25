<template>
  <div class="flex w-full h-100 overflow-y-auto">
    <div
      @click="
        $event.target.tagName === 'DIV' &&
          textEditor.editor?.chain?.().focus?.().run?.()
      "
      class="mx-auto cursor-text min-h-full w-full md:w-auto ps-4 md:p-0"
    >
      <FTextEditor
        :key="editorExtensions.length"
        ref="textEditor"
        class="min-w-full md:min-w-[65ch]"
        :editor-class="[
          'prose-sm min-h-[4rem]',
          `text-[${writerSettings.doc?.font_size || 15}px]`,
          `leading-[${writerSettings.doc?.line_height || 1.5}]`,
          writerSettings.doc?.custom_css,
        ]"
        :content="rawContent"
        :editable="!!entity.write"
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
            rawContent = val
            yjsContent = Y.encodeStateAsUpdate(doc)
            if (db)
              db.transaction(['content'], 'readwrite')
                .objectStore('content')
                .put({ val, saved: new Date() }, props.entity.name)
            edited = true
            autosave()
          }
        "
        :mentions="users"
        placeholder="Start writing here..."
        :bubble-menu="bubbleMenuButtons"
        :extensions="editorExtensions"
      />
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
  debounce,
  useFileUpload,
  useDoc,
} from "frappe-ui"
import { v4 as uuidv4 } from "uuid"
import {
  computed,
  defineAsyncComponent,
  reactive,
  onMounted,
  ref,
  onBeforeUnmount,
  h,
  watch,
} from "vue"
import store from "@/store"
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
import { TiptapCollabProvider } from "@hocuspocus/provider"
import Collaboration from "@tiptap/extension-collaboration"
import * as Y from "yjs"

import H1 from "./icons/h-1.vue"
import H2 from "./icons/h-2.vue"
import H3 from "./icons/h-3.vue"

import LucideMessageCircle from "~icons/lucide/message-circle"

const textEditor = ref("textEditor")
const editor = computed(() => {
  let editor = textEditor.value?.editor
  console.log(editor)
  return editor
})
defineExpose({ editor })

const rawContent = defineModel("rawContent")
const yjsContent = defineModel("yjsContent")
const showComments = defineModel("showComments")
const edited = defineModel("edited")

const props = defineProps({
  entity: Object,
  showResolved: Boolean,
  users: Object,
})
const comments = ref([])

const emit = defineEmits(["updateTitle", "saveDocument", "mentionedUsers"])
const activeComment = ref(null)
const autosave = debounce(() => emit("saveDocument"), 2000)

const writerSettings = useDoc({
  doctype: "Drive Settings",
  name: store.state.user.id,
  immediate: true,
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

// Disables garbage collection
const doc = new Y.Doc({ gc: false })
if (yjsContent.value) Y.applyUpdate(doc, yjsContent.value)
const editorExtensions = [
  CharacterCount,
  FontFamily.configure({
    types: ["textStyle"],
  }),
  Collaboration.configure({
    document: doc,
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

onMounted(() => {
  const orderedComments = getOrderedComments(editor.value.state.doc)
  comments.value = props.entity.comments.toSorted((a, b) => {
    const pos1 = orderedComments.findIndex((k) => k.id === a.name)
    const pos2 = orderedComments.findIndex((k) => k.id === b.name)
    return pos1 - pos2
  })

  const provider = new TiptapCollabProvider({
    name: props.entity.name, // Document identifier
    appId: "ok01lqjm",
    token:
      "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NTYxMTE5NTAsIm5iZiI6MTc1NjExMTk1MCwiZXhwIjoxNzU2MTk4MzUwLCJpc3MiOiJodHRwczovL2Nsb3VkLnRpcHRhcC5kZXYiLCJhdWQiOiJvazAxbHFqbSJ9.XRfbjwkjdOdWric-cTqcGB3XvRqMOzMeBkOf0lNxswU",
    document: doc,
    user: store.state.user.id,
  })
  editorExtensions.push(
    CollaborationCursor.configure({
      provider,
      user: {
        name: store.state.user.fullName,
        avatar: store.state.user.imageURL,
        color: getRandomColor(),
      },
    })
  )
})

onBeforeUnmount(() => {
  comments.value
    .filter((k) => k.new)
    .filter(({ name }) => editor.value.commands.unsetComment(name))
})

onKeyDown("Enter", evalImplicitTitle)
onKeyDown("S", (e) => {
  if (!e.metaKey) {
    return
  }
  e.preventDefault()
  emit("saveDocument") &&
    toast({
      title: "Document saved",
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
  if (!props.entity.write) return
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
