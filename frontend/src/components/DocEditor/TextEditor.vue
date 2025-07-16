<template>
  <div class="flex w-full h-100 overflow-y-auto">
    <div
      class="mx-auto"
      :class="
        comments.filter((k) => !k.resolved).length
          ? 'w-[60%]'
          : 'w-[90%] sm:w-[80%]'
      "
    >
      <FTextEditor
        ref="textEditor"
        editor-class="prose-sm min-h-[4rem] p-2"
        :content="rawContent"
        :editable="!!entity.write"
        @change="
          (val) => {
            rawContent = val
            if (db)
              db.transaction(['content'], 'readwrite')
                .objectStore('content')
                .put(val, props.entity.name)
            autosave()
          }
        "
        :mentions="users"
        placeholder="Start writing here..."
        :bubble-menu="bubbleMenuButtons"
        :show-bubble-menu-always="true"
        :extensions="editorExtensions"
      />
    </div>
    <FloatingComments
      v-if="comments.length"
      :entity-name="entity.name"
      :editor
      v-model:active-comment="activeComment"
      v-model:comments="comments"
    />
  </div>
</template>

<script setup>
import { toast } from "@/utils/toasts.js"
import { TextEditor as FTextEditor, debounce } from "frappe-ui"
import { v4 as uuidv4 } from "uuid"
import {
  computed,
  defineAsyncComponent,
  onMounted,
  reactive,
  ref,
  onBeforeUnmount,
  h,
  watch,
} from "vue"
import store from "@/store"
import { FontFamily } from "./extensions/font-family"
import CommentExtension from "@sereneinserenade/tiptap-comment-extension"
import FloatingComments from "./components/FloatingComments.vue"
import { printDoc } from "@/utils/files"
import { onKeyDown } from "@vueuse/core"
import emitter from "@/emitter"

import H1 from "./icons/h-1.vue"
import H2 from "./icons/h-2.vue"
import H3 from "./icons/h-3.vue"
import LucideWifi from "~icons/lucide/wifi"
import LucideWifiOff from "~icons/lucide/wifi-off"
import LucideMessageCircle from "~icons/lucide/message-circle"

const autosave = debounce(() => emit("saveDocument"), 5000)
const textEditor = ref("textEditor")
const editor = computed(() => {
  let editor = textEditor.value?.editor
  return editor
})

const rawContent = defineModel()
const props = defineProps({
  entity: Object,
  isWritable: Boolean,
  users: Object,
})
const comments = ref([])

const emit = defineEmits(["updateTitle", "saveDocument", "mentionedUsers"])
const activeComment = ref(null)

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
  FontFamily.configure({
    types: ["textStyle"],
  }),
  ExtendedCommentExtension.configure({
    HTMLAttributes: {
      class: "",
    },
    onCommentActivated: (id) => {
      if (id) {
        console.log("ACTIVATED", id)
        activeComment.value = id
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
  action: (editor) => {
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
      replies: [],
    }
    console.log(newComment)
    comments.value = [...comments.value, newComment].toSorted((a, b) => {
      const pos1 = orderedComments.findIndex((k) => k.id === a.name)
      const pos2 = orderedComments.findIndex((k) => k.id === b.name)
      return pos1 - pos2
    })
    activeComment.value = id
  },
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
})
onBeforeUnmount(() => {
  comments.value
    .filter((k) => k.new)
    .filter(({ name }) => editor.value.commands.unsetComment(name))
})

onKeyDown("S", (e) => {
  if (!(e.ctrlKey || e.metaKey)) {
    return
  }
  e.preventDefault()
  emit("mentionedUsers", this.parseMentions(this.editor.getJSON()))
  if (this.synced || this.peercount === 0) {
    emit("saveDocument")
  }
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

window.addEventListener("offline", () => {
  toast({
    title: "You're offline",
    icon: LucideWifiOff,
    text: "Don't worry, your changes will be saved locally.",
  })
})
window.addEventListener("online", () => {
  toast({ title: "Back online!", icon: h(LucideWifi) })
})

// Local saving
const db = ref()
watch(db, (db) => {
  db
    .transaction(["content"])
    .objectStore("content")
    .get(props.entity.name).onsuccess = (val) => {
    // Hack until we get versioning.
    if (val.target.result.length > 20) rawContent.value = val.target.result
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
  this.implicitTitle = this.editor.state.doc.firstChild.textContent
    .replaceAll("#", "")
    .replaceAll("@", "")
    .slice(0, 35)
    .trim()
  if (
    this.implicitTitle.length === 0 ||
    this.entity.title === this.implicitTitle
  )
    return
  if (this.implicitTitle.length) {
    store.state.activeEntity.title = this.implicitTitle
    this.$resources.rename.submit({
      entity_name: props.entity.name,
      new_title: this.implicitTitle,
    })
  }
}
</script>

<style>
@import url("./editor.css");
</style>
