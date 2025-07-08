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
        @change="
          (val) => {
            rawContent = val
            db.transaction(['content'], 'readwrite')
              .objectStore('content')
              .put(val, props.entity.name)
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
      :entity-name="entity.name"
      :editor
      v-model:active-comment="activeComment"
      v-model:comments="comments"
    />
  </div>

  <!-- <DocMenuAndInfoBar
    v-if="editor && ready"
    ref="MenuBar"
    v-model:all-annotations="allAnnotations"
    v-model:active-annotation="activeAnnotation"
    :editor="editor"
    :versions="versions"
    :settings="settings"
  /> -->
  <!-- <div
      :class="[
        settings.docFont,
        settings.docSize ? 'text-[15px]' : 'text-[17px]',
        settings.docWidth
          ? 'sm:min-w-[75vw] sm:max-w-[75vw]'
          : 'sm:min-w-[21cm] sm:max-w-[21cm]',
      ]"
      class="flex sm:w-full items-start justify-start lg:justify-center mx-auto px-[1cm]"
    >
   
      <editor-content
        id="editor-capture"
        class="min-w-full"
        autocomplete="true"
        autocorrect="true"
        autocapitalize="true"
        :spellcheck="settings.docSpellcheck ? true : false"
        :editor="editor"
        @keydown.enter.passive=" this.entity.title === "Untitled Document" && evalImplicitTitle()"
      />
    </div>
  </div>
  
  <FilePicker
    v-if="showFilePicker"
    v-model="showFilePicker"
    :suggested-tab-index="0"
    @success="
      (val) => {
        pickedFile = val
        showFilePicker = false
        if (editor) {
          if (editable) {
            wordToHTML()
          }
        }
      }
    "
  />
  <SnapshotPreviewDialog
    v-if="snapShotDialog"
    v-model="snapShotDialog"
    :snapshot-data="selectedSnapshot"
    @success="
      () => {
        selectedSnapshot = null
      }
    "
  />
  -->
</template>

<script setup>
import FilePicker from "@/components/FilePicker.vue"
import { toast } from "@/utils/toasts.js"
import Link from "@tiptap/extension-link"
import TaskItem from "@tiptap/extension-task-item"
import TaskList from "@tiptap/extension-task-list"
import Typography from "@tiptap/extension-typography"
import StarterKit from "@tiptap/starter-kit"
import {
  onOutsideClickDirective,
  createDocumentResource,
  createListResource,
  TextEditor as FTextEditor,
  debounce,
} from "frappe-ui"
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
import { IndexeddbPersistence } from "y-indexeddb"
import { WebrtcProvider } from "y-webrtc"
import * as Y from "yjs"
import { uploadDriveEntity } from "@/utils/chunkFileUpload"
import { detectMarkdown, markdownToHTML } from "@/utils/markdown"
import DocMenuAndInfoBar from "./components/DocMenuAndInfoBar.vue"
import configureMention from "./extensions/mention/mention"
import { Table } from "./extensions/table"
import TableBubbleMenu from "./components/TableBubbleMenu.vue"
import { PageBreak } from "./extensions/Pagebreak"
import { Highlight } from "./extensions/backgroundColor"
import { CharacterCount } from "./extensions/character-count"
import { Collaboration } from "./extensions/collaboration"
import { CollaborationCursor } from "./extensions/collaborationCursor"
import { Color } from "./extensions/color"
import { FontFamily } from "./extensions/font-family"
import CommentExtension from "@sereneinserenade/tiptap-comment-extension"

import { FontSize } from "./extensions/font-size"
import { Indent } from "./extensions/indent"
import { LineHeight } from "./extensions/lineHeight"
import { Placeholder } from "./extensions/placeholder"
import { TextAlign } from "./extensions/text-align"
import { TextStyle } from "./extensions/text-style"
import { Underline } from "./extensions/underline"
import { ResizableMedia } from "./extensions/resizenode"
import { createEditorButton } from "./utils"
import { Annotation } from "./extensions/AnnotationExtension/annotation"
import suggestion from "./extensions/suggestion/suggestion"
import Commands from "./extensions/suggestion/suggestionExtension"
import SnapshotPreviewDialog from "./components/SnapshotPreviewDialog.vue"
import { DiffMarkExtension } from "./extensions/createDiffMark"
import FloatingComments from "./components/FloatingComments.vue"
import { printDoc } from "@/utils/files"
import emitter from "@/emitter"
import { onKeyDown } from "@vueuse/core"
import H1 from "./icons/h-1.vue"
import H2 from "./icons/h-2.vue"
import H3 from "./icons/h-3.vue"
import LucideWifi from "~icons/lucide/wifi"
import LucideWifiOff from "~icons/lucide/wifi-off"
import LucideMessageCircle from "~icons/lucide/message-circle"
import store from "@/store"

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

const font = ref("font-sans")
const localStore = ref(null)
const implicitTitle = ref(null)
const allComments = reactive([])
const allAnnotations = reactive([])
const activeComment = ref(null)

const versions = reactive([])
const selectedSnapshot = ref(null)
const snapShotDialog = ref(false)

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
        (commentId) =>
        ({ state, tr, dispatch }) => {
          const { doc } = state
          const markType = state.schema.marks[this.name]

          doc.descendants((node, pos) => {
            if (!node.isText) return true
            node.marks.forEach((mark) => {
              if (
                mark.type === markType &&
                mark.attrs.commentId === commentId &&
                !mark.attrs.resolved
              ) {
                const updatedMark = markType.create({
                  ...mark.attrs,
                  resolved: true,
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
  {
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

      comments.value = [...comments.value, newComment].toSorted((a, b) => {
        const pos1 = orderedComments.findIndex((k) => k.id === a.name)
        const pos2 = orderedComments.findIndex((k) => k.id === b.name)
        return pos1 - pos2
      })
      activeComment.value = id
    },
    isActive: () => false,
  },
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
// provide() {
//   return {
//     editor: computed(() => this.editor),
//     document: computed(() => this.document),
//     versions: computed(() => this.versions),
//   }
// },
// inheritAttrs: false,
//expose: ["editor", "versions"],

// docWidth: this.settings.docWidth,
// docSize: this.settings.docSize,
// docFont: this.settings.docFont,
// buttons: [],
// forceHideBubbleMenu: false,
// synced: false,
// peercount: 0,
// ready: true,
// document: null,
// awareness: null,

// showCommentMenu: false,
// commentText: "",
// isCommentModeOn: true,
// showFilePicker: false,
// pickedFile: null,
// activeCommentsInstance: {
//   uuid: "",
//   comments: [],
// },

// activeAnchorAnnotations: null,

// activeAnchorAnnotations: {
//   handler(newVal) {
//     if (newVal) {
//       // unexpected case??
//       let yArray = this.document.getArray("docAnnotations")
//       // Toggle visibility if it's not visible in the document anymore
//       yArray.forEach((item) => {
//         if (newVal.has(item.get("id"))) {
//           item.set("anchor", 1)
//         } else {
//           item.set("anchor", 0)
//         }
//       })
//     }
//   },
// },
// lastSaved(newVal) {
//   const ymap = this.document.getMap("docinfo")
//   const lastSaved = ymap.get("lastsaved")
//   if (newVal > lastSaved) {
//     ymap.set("lastsaved", newVal)
//   }
// },
// settings(newVal) {
//   switch (newVal.toLowerCase()) {
//     case "sans":
//       this.defaultFont = "font-['Nunito']"
//       break
//     case "serif":
//       this.defaultFont = "font-['Lora']"
//       break
//     case "round":
//       this.defaultFont = "font-['Nunito']"
//       break
//     case "mono":
//       this.defaultFont = "font-['Geist-Mono']"
//       break
//     default:
//       this.defaultFont = "font-['InterVar']"
//   }
// },
//   activeCommentsInstance: {
//     handler(newVal) {
//       if (newVal) {
//         // check if userid is available
//         store.commit(
//           "setActiveCommentsInstance",
//           JSON.stringify(newVal)
//         )
//       }
//     },
//     immediate: true,
//   },
//   allComments: {
//     handler(newVal) {
//       if (newVal) {
//         store.commit("setAllComments", JSON.stringify(newVal))
//       }
//     },
//     immediate: true, // make this watch function is called when component created
//   },
//   editable(value) {
//     this.editor.setEditable(value)
//   },
// },

emitter.on("printFile", () => {
  if (this.editor) {
    this.printEditorContent()
  }
})

emitter.on("importDocFromWord", () => {
  this.showFilePicker = true
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
// this.editor = new Editor({
//   editable: this.editable,
//   autofocus: "start",
//   editorProps: {
//     attributes: {
//       class: normalizeClass([`prose prose-sm`]),
//     },
//     clipboardTextParser: (text, $context) => {
//       if (!detectMarkdown(text)) return
//       let dom = document.createElement("div")
//       dom.innerHTML = markdownToHTML(text)
//       let parser =
//         this.editor.view.someProp("clipboardParser") ||
//         this.editor.view.someProp("domParser") ||
//         DOMParser.fromSchema(this.editor.schema)
//       return parser.parseSlice(dom, {
//         preserveWhitespace: true,
//         context: $context,
//       })
//     },
//   })

// evaluate document version
// onUpdate() {
//componentContext.updateConnectedUsers(componentContext.editor)
//componentContext.findCommentsAndStoreValues()
// componentContext.setCurrentComment()
// if (
//   componentContext.$props.rawContent ===
//   componentContext.editor.getHTML()
// )
//   return
// componentContext.$emit(
//   "update:rawContent",
//   componentContext.editor.getHTML()
// )
// componentContext.$emit(
//   "mentionedUsers",
//   componentContext.parseMentions(componentContext.editor.getJSON())
// )
// componentContext.$emit(
//   "update:yjsContent",
//   Y.encodeStateAsUpdate(componentContext.document)
// )
// componentContext.updateAnnotationStatus()
// onSelectionUpdate() {
//   //componentContext.updateConnectedUsers(componentContext.editor)
//   //componentContext.setCurrentComment()
//   //componentContext.isTextSelected =
//   //  !!componentContext.editor.state.selection.content().size
// },
// eslint-disable-next-line no-sparse-arrays
//   extensions: [
//     StarterKit.configure({
//       history: false,
//       paragraph: {
//         HTMLAttributes: {
//           class: this.entity.version == 0 ? "legacy" : "",
//         },
//       },
//       heading: {
//         levels: [1, 2, 3, 4, 5],
//       },
//       listItem: {
//         HTMLAttributes: {
//           class: "prose-list-item",
//         },
//       },
//       codeBlock: {
//         HTMLAttributes: {
//           spellcheck: false,
//         },
//       },
//       blockquote: {
//         HTMLAttributes: {},
//       },
//       code: {
//         HTMLAttributes: {},
//       },
//       bulletList: {
//         keepMarks: true,
//         keepAttributes: false,
//         HTMLAttributes: {
//           class: "",
//         },
//       },
//       orderedList: {
//         keepMarks: true,
//         keepAttributes: false,
//         HTMLAttributes: {
//           class: "",
//         },
//       },
//     }),
//     Commands.configure({
//       suggestion,
//     }),
//     Table,
//     FontFamily.configure({
//       types: ["textStyle"],
//     }),
//     TextAlign.configure({
//       types: ["heading", "paragraph"],
//       defaultAlignment: "left",
//     }),
//     ,
//     PageBreak,
//     Annotation.configure({
//       onAnnotationClicked: (ID) => {
//         componentContext.setAndFocusCurrentAnnotation(ID)
//       },
//       onAnnotationActivated: (ID) => {
//         //this.activeAnnotation = ID
//         if (ID) setTimeout(() => componentContext.setCurrentAnnotation(ID))
//       },
//       HTMLAttributes: {
//         //class: 'cursor-pointer annotation  annotation-number'
//         //class: 'cursor-pointer bg-amber-300 bg-opacity-20 border-b-2 border-yellow-300 pb-[1px]'
//         class: "cursor-pointer annotation",
//       },
//     }),

//     LineHeight,
//     Indent,
//     Link.configure({
//       openOnClick: false,
//     }),
//     Placeholder.configure({
//       placeholder: "Press / for commands",
//     }),
//     Highlight.configure({
//       multicolor: true,
//     }),
//     configureMention(this.userList),
//     TaskList.configure({
//       HTMLAttributes: {},
//     }),
//     TaskItem.configure({
//       HTMLAttributes: {
//         class: "my-task-item",
//       },
//     }),
//     CharacterCount,
//     Underline,
//     Typography,
//     TextStyle,
//     FontSize.configure({
//       types: ["textStyle"],
//     }),
//     Color.configure({
//       types: ["textStyle"],
//     }),
//     ResizableMedia.configure({
//       uploadFn: (file) =>
//         uploadDriveEntity(file, this.entity.team, this.entityName),
//     }),
//     DiffMarkExtension,
//   ],
// })

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

const db = ref()
const request = window.indexedDB.open("Writer", 1)
request.onsuccess = (event) => {
  db.value = event.target.result
}
request.onupgradeneeded = () => {
  if (!request.result.objectStoreNames.contains("content"))
    request.result.createObjectStore("content")
}
watch(db, (db) => {
  db
    .transaction(["content"])
    .objectStore("content")
    .get(props.entity.name).onsuccess = (val) => {
    if (val.target.result) rawContent.value = val.target.result
  }
})

function beforeUnmount() {
  emitter.off("printFile")
  emitter.off("importDocFromWord")

  this.editor.destroy()
  this.editor = null
}

function updateAnnotationStatus() {
  const temp = new Set()
  this.editor.state.doc.descendants((node) => {
    const { marks } = node
    marks.forEach((mark) => {
      if (mark.type.name === "annotation") {
        const annotationMark = mark.attrs.annotationID
        temp.add(annotationMark)
      }
    })
  })
  this.activeAnchorAnnotations = temp
}

async function wordToHTML() {
  let ctx = this
  if (
    ctx.pickedFile?.mime_type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
    ctx.pickedFile?.file_ext == ".docx"
  ) {
    const headers = {
      Accept: "application/json",
      "Content-Type": "application/json; charset=utf-8",
      "X-Frappe-Site-Name": window.location.hostname,
      Range: "bytes=0-10000000",
    }
    const res = await fetch(
      `/api/method/drive.api.files.get_file_content?entity_name=${ctx.pickedFile.name}`,
      {
        method: "GET",
        headers,
      }
    )
    if (res.ok) {
      let blob = await res.arrayBuffer()
      const { convertToHtml } = await import("mammoth")
      convertToHtml({ arrayBuffer: blob })
        .then(function (result) {
          ctx.editor.commands.insertContent(result.value)
        })
        .catch(function (error) {
          console.error(error)
        })
    }
  } else {
    toast({
      title: "Not a valid DOCX file!",
      position: "bottom-right",
      icon: "alert-triangle",
      iconClasses: "text-ink-red-3",
      timeout: 2,
    })
  }
}

function printEditorContent() {
  const html = this.editor.getHTML()
  if (html) {
    printDoc(html)
    return true
  }
  return false
}
function shouldShow({ state }) {
  const { from, to } = state.selection
  // Check if the selection is within a text node
  const node = state.doc.nodeAt(from)
  if (node && node.type.name === "text") {
    // Ensure the selection is not empty
    return from !== to
  }
  return false // Hide the menu if the selection is outside a text node
}
function RndColor() {
  const max = 255
  const min = 100
  const range = max - min
  const red = Math.floor(Math.random() * range) + min
  const green = Math.floor(Math.random() * range) + min
  const blue = Math.floor(Math.random() * range) + min
  const redToHex = red.toString(16)
  const greenToHex = green.toString(16)
  const blueToHex = blue.toString(16)
  return "#" + redToHex + greenToHex + blueToHex
}
function discardComment() {
  this.commentText = ""
  this.isCommentModeOn = false
}
function getIsCommentModeOn() {
  return this.isCommentModeOn
}

function focusContent({ from, to }) {
  this.editor.chain().setTextSelection({ from, to }).run()
}
function findCommentsAndStoreValues() {
  const tempComments = []
  this.editor.state.doc.descendants((node, pos) => {
    const { marks } = node
    marks.forEach((mark) => {
      if (mark.type.name === "comment") {
        const markComments = mark.attrs.comment
        const jsonComments = markComments ? JSON.parse(markComments) : null
        if (
          jsonComments !== null &&
          !tempComments.find((el) => el.jsonComments.uuid === jsonComments.uuid)
        ) {
          tempComments.push({
            node,
            jsonComments,
            from: pos,
            to: pos + (node.text?.length || 0),
            text: node.text,
          })
        }
      }
    })
  })
  return (this.allComments = tempComments)
}

function setCurrentAnnotation() {
  let newVal = this.editor.isActive("annotation")
  const sideBarState = store.state.showInfo && this.$refs.MenuBar.tab == 5
  if (newVal && sideBarState) {
    this.activeAnnotation = this.editor.getAttributes("annotation").annotationID
  }
}
function setAndFocusCurrentAnnotation() {
  let newVal = this.editor.isActive("annotation")
  if (newVal) {
    store.state.showInfo = true
    this.$refs.MenuBar.tab = 5
    this.activeAnnotation = this.editor.getAttributes("annotation").annotationID
  }
}
function setCurrentComment() {
  let newVal = this.editor.isActive("comment")
  if (newVal) {
    store.state.showInfo = true
    this.$refs.MenuBar.tab = 5
    const parsedComment = JSON.parse(
      this.editor.getAttributes("comment").comment
    )
    parsedComment.comments =
      typeof parsedComment.comments === "string"
        ? JSON.parse(parsedComment.comments)
        : parsedComment.comments
    this.activeCommentsInstance = parsedComment
  } else {
    this.activeCommentsInstance = {}
  }
}
function setComment(val) {
  const localVal = val || this.commentText
  if (!localVal.trim().length) return
  const currentSelectedComment = JSON.parse(
    JSON.stringify(this.activeCommentsInstance)
  )
  const commentsArray =
    typeof currentSelectedComment.comments === "string"
      ? JSON.parse(currentSelectedComment.comments)
      : currentSelectedComment.comments
  if (commentsArray) {
    commentsArray.push({
      userName: store.state.user.id,
      userImage: store.state.user.imageURL,
      time: Date.now(),
      content: localVal,
    })
    const commentWithUuid = JSON.stringify({
      uuid: this.activeCommentsInstance.uuid || uuidv4(),
      comments: commentsArray,
    })
    this.editor.chain().setComment(commentWithUuid).run()
    this.commentText = ""
  } else {
    const commentWithUuid = JSON.stringify({
      uuid: uuidv4(),
      comments: [
        {
          userName: store.state.user.id,
          userImage: store.state.user.imageURL,
          time: Date.now(),
          content: localVal,
        },
      ],
    })
    this.editor.chain().setComment(commentWithUuid).run()
    this.commentText = ""
  }
}
function parseMentions(data) {
  const tempMentions = (data.content || []).flatMap(this.parseMentions)
  if (data.type === "mention") {
    tempMentions.push({
      id: data.attrs.id,
      author: data.attrs.author,
      type: data.attrs.type,
    })
  }
  const uniqueMentions = [...new Set(tempMentions.map((item) => item.id))].map(
    (id) => tempMentions.find((item) => item.id === id)
  )
  return uniqueMentions
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

// rename() {
//   return {
//     url: "drive.api.files.call_controller_method",
//     makeParams: (params) => ({
//       method: "rename",
//       ...params,
//     }),
//     onSuccess: () => {
//       store.state.breadcrumbs[
//         store.state.breadcrumbs.length - 1
//       ].label = this.implicitTitle
//     },
//     debounce: 500,
//   }
// },
</script>

<style>
@import url("./editor.css");

.collaboration-cursor__caret {
  border-left: 0px solid currentColor;
  border-right: 2px solid currentColor;
  margin-left: 0px;
  margin-right: -2px;
  pointer-events: none;
  position: relative;
  word-break: normal;
}
/* Render the username above the caret */
.collaboration-cursor__label {
  border-radius: 60px;
  border: 2px solid #0000001a;
  color: #ffffffdf;
  font-size: 0.65rem;
  font-style: normal;
  font-family: "Inter";
  font-weight: 500;
  line-height: normal;
  padding: 0.1rem 0.25rem;
  position: absolute;
  top: -1.5em;
  left: 0.25em;
  user-select: none;
  white-space: nowrap;
}

summary {
  display: flex;
  width: 100%;
  padding: 0 2.5rem;
  box-sizing: border-box;
  pointer-events: none;
  outline: none;
}

summary p {
  margin-top: 0.15rem !important;
  margin-bottom: 0.15rem !important;
}

.grip-row.selected {
  background-color: #e3f0fce2;
  content: "✓";
}
.grip-column.selected {
  background-color: #e3f0fce2;
}

.grip-column.selected::before {
  content: "✓";
  position: absolute;
  color: white;
  top: -25%;
  left: 0%;
  font-weight: 600;
}

.grip-row.selected::before {
  content: "✓";
  position: absolute;
  color: white;
  top: -25%;
  left: 0%;
  font-weight: 600;
}
</style>
