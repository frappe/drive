<template>
  <div class="flex flex-col w-full">
    <TextEditorFixedMenu
      v-if="editor && editable && !settings.minimal && !current"
      class="w-full max-w-[100vw] overflow-x-auto border-b border-outline-gray-modals justify-start md:justify-center py-1.5 shrink-0"
      :buttons="menuButtons"
    />
    <div
      v-if="current"
      class="bg-surface-gray-2 text-ink-gray-8 p-3 text-base flex justify-between items-center"
    >
      <div class="flex flex-col gap-1">
        <div v-if="current.manual">
          <span class="font-medium">{{ current.title }}</span>
        </div>
        <div v-else>
          This is a automatic snapshot of this document from
          {{ formatDate(current.title) }}.
        </div>
        <div class="text-xs text-ink-gray-5">
          Editing is disabled until you exit this preview.
        </div>
      </div>
      <div class="flex gap-2">
        <Button
          variant="ghost"
          label="Exit"
          class="hover:!bg-surface-gray-2 hover:underline"
          @click="emitter.emit('clear-snapshot')"
        />
        <Button
          variant="solid"
          label="Restore"
          @click="emitter.emit('restore-snapshot', current)"
        />
      </div>
    </div>
    <div
      id="editorScrollContainer"
      class="flex-1 flex w-full overflow-y-auto"
    >
      <div
        class="mx-auto cursor-text w-full flex justify-center h-full"
        :class="current ? 'pb-15' : ''"
        @click="
          $event.target.tagName === 'DIV' &&
            textEditor.editor?.chain?.().focus?.().run?.()
        "
      >
        <FTextEditor
          v-if="
            !collab ||
            editorExtensions.find((k) => k.name === 'collaborationCursor') ||
            !isFrappeDoc
          "
          :key="editorExtensions.length"
          ref="textEditor"
          class="min-w-full h-full flex flex-col"
          :editor-class="[
            'prose-sm min-h-full mx-auto px-10 overflow-x-auto py-14',
            `text-[${settings?.font_size || 15}px]`,
            `leading-[${settings?.line_height || 1.5}]`,
            settings?.wide
              ? 'md:min-w-[100ch] md:max-w-[100ch]'
              : 'md:min-w-[48rem] md:max-w-[48rem]',
            current ? 'pb-24' : '',
          ]"
          :content="!collab ? rawContent : undefined"
          :editable
          :upload-function="
            (file) => {
              const fileUpload = useFileUpload()
              return fileUpload.upload(file, {
                params: { doc: entity.name },
                upload_endpoint: `/api/method/drive.api.files.upload_embed`,
              })
            }
          "
          :mentions="{ mentions: users, selectable: false }"
          placeholder="Start writing here..."
          :bubble-menu="settings.minimal && menuButtons"
          :extensions="editorExtensions"
          :autofocus="true"
          @change="
            (val) => {
              if (val === rawContent || current) return
              rawContent = val
              if (collab) yjsContent = Y.encodeStateAsUpdate(doc)
              if (db)
                db.transaction(['content'], 'readwrite')
                  .objectStore('content')
                  .put({ val, saved: new Date() }, props.entity.name)
              if (!editable) return
              edited = true
              autosave()
              autoversion?.()
            }
          "
        >
          <template #editor="{ editor }">
            <EditorContent
              :style="{
                fontFamily: `var(--font-${settings?.font_family})`,
              }"
              :editor="editor"
            />
          </template>
        </FTextEditor>
      </div>
      <ToC
        v-show="anchors.length > 1"
        :editor
        :anchors
        :class="editable ? 'top-24' : 'top-15'"
      />
      <FloatingComments
        v-if="comments.length"
        v-model:show-comments="showComments"
        v-model:active-comment="activeComment"
        v-model:comments="comments"
        :entity="entity"
        :editor
        @save="console.log('recieved'), $emit('saveComment')"
      />
    </div>
  </div>
</template>

<script setup>
import {
  TextEditor as FTextEditor,
  TextEditorFixedMenu,
  createResource,
  debounce,
  useFileUpload,
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
  inject,
  provide,
} from "vue"
import { EditorContent } from "@tiptap/vue-3"
import { toUint8Array } from "js-base64"
import * as Y from "yjs"
import { IndexeddbPersistence } from "y-indexeddb"
import { ySyncPluginKey } from "y-prosemirror"
import { WebrtcProvider } from "y-webrtc"
import Collaboration from "@tiptap/extension-collaboration"
import { onKeyDown } from "@vueuse/core"
import {
  default as TableOfContents,
  getHierarchicalIndexes,
} from "@tiptap/extension-table-of-contents"

import H1 from "./icons/h-1.vue"
import H2 from "./icons/h-2.vue"
import H3 from "./icons/h-3.vue"
import LucideMessageCircle from "~icons/lucide/message-circle"

import store from "@/store"
import emitter from "@/emitter"
import { rename } from "@/resources/files"
import { printDoc, getRandomColor, dynamicList } from "@/utils/files"
import { formatDate } from "@/utils/format"
import { toast } from "@/utils/toasts"
import FontFamily from "./extensions/font-family"
import FloatingQuoteButton from "./extensions/comment"
import MediaDownload from "./extensions/media-download"
import ExtendedCommentExtension from "./extensions/extended-comment"
import { CharacterCount } from "./extensions/character-count"
import { CollaborationCursor } from "./extensions/collaboration-cursor"
import { FontSize } from "./extensions/font-size"
import EmbedExtension from "./extensions/embed-extension"
import FloatingComments from "./components/FloatingComments.vue"

const rawContent = defineModel("rawContent")
const yjsContent = defineModel("yjsContent")
const showComments = defineModel("showComments")
const current = defineModel("current")
const edited = defineModel("edited")

const props = defineProps({
  entity: Object,
  settings: Object,
  editable: Boolean,
  isFrappeDoc: Boolean,
  showResolved: Boolean,
  users: Object,
  currentVersion: { required: false, type: Object },
})
const emit = defineEmits(["newVersion", "saveComment", "saveDocument"])
const inIframe = inject("inIframe")

const comments = ref([])
const anchors = ref([])
const activeComment = ref(null)

const textEditor = ref("textEditor")
const editor = computed(() => {
  const editor = textEditor.value?.editor
  return editor
})
provide("editor", editor)
const scrollParent = computed(() =>
  document.querySelector("#editorScrollContainer")
)
defineExpose({ editor })

const autosave = debounce(() => emit("saveDocument"), 2000)
let autoversion

watch(
  () => props.settings,
  (val, prev) => {
    if (val.versioning === prev?.versioning && autoversion) return
    const duration = Math.max(0.9, +val.versioning - 1) * 1000
    autoversion = debounce(() => {
      if (!collab.value) return
      const snap = Y.snapshot(doc)
      const prevVersion =
        props.entity.versions[props.entity.versions.length - 1]
      const prevSnapshot = prevVersion
        ? Y.decodeSnapshot(toUint8Array(prevVersion.snapshot))
        : Y.emptySnapshot
      if (prevVersion != null) {
        // account for the action of adding a version to ydoc
        prevSnapshot.sv.set(
          prevVersion.clientID,
          prevSnapshot.sv.get(prevVersion.clientID) + 1
        )
      }
      if (!Y.equalSnapshots(prevSnapshot, snap)) {
        emit("newVersion", Y.encodeSnapshot(snap), +props.settings.versioning)
      }
    }, duration)
  }
)

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

const editorExtensions = [
  FontSize,
  CharacterCount,
  TableOfContents.configure({
    onUpdate: (val) => (anchors.value = val),
    getIndex: getHierarchicalIndexes,
    scrollParent: () => scrollParent.value,
  }),
  FontFamily.configure({
    types: ["textStyle"],
  }),
  EmbedExtension,
  props.entity.comment &&
    !inIframe &&
    FloatingQuoteButton.configure({
      onClick: () => {
        createNewComment(editor.value)
      },
    }),
  ExtendedCommentExtension.configure({
    onCommentActivated: (id) => {
      const isResolved = comments.value.find((k) => id === k.name)?.resolved
      if (id && (!isResolved || showResolved)) {
        activeComment.value = id
        showComments.value = true
        const commentEl = document.querySelector(
          `span[data-comment-id="${id}"]`
        )
        if (!commentEl.offsetParent)
          commentEl.scrollIntoView({
            behavior: "smooth",
            block: "start",
            inline: "nearest",
          })
      }
    },
  }),
  MediaDownload,
]

let prov, doc, localstorage
const collab = computed(() => props.settings?.collab)
import { yDocToProsemirrorJSON } from "y-prosemirror"
import { Editor } from "@tiptap/core"
import { isModKey } from "@/utils/files"

if (collab.value) {
  doc = new Y.Doc({ gc: true })
  localstorage = new IndexeddbPersistence("fdoc-" + props.entity.name, doc) // eslint-disable-line
  if (yjsContent.value) Y.applyUpdate(doc, yjsContent.value)

  prov = new WebrtcProvider("fdoc-" + props.entity.name, doc, {
    signaling: ["wss://signal.frappe.cloud"],
    peerOpts: {
      config: {
        iceServers: [
          { urls: "stun:stun.l.google.com:19302" },
          {
            urls: [
              "turn:signal.frappe.cloud:3478?transport=udp",
              "turn:signal.frappe.cloud:3478?transport=tcp",
            ],
            username: "turnuser",
            credential: "turnpass",
          },
        ],
      },
    },
  })
  const permanentUserData = new Y.PermanentUserData(doc)
  permanentUserData.setUserMapping(doc, doc.clientID, store.state.user.id)
  const colors = [
    { light: "#ecd44433", dark: "#ecd444" },
    { light: "#ee635233", dark: "#ee6352" },
    { light: "#6eeb8333", dark: "#6eeb83" },
  ]
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
        id: store.state.user.id,
        avatar: store.state.user.imageURL,
        color: getRandomColor(),
      },
    })
  )
}

const menuButtons = computed(() =>
  dynamicList([
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
    ["Bullet List", "Numbered List", "Task List"],
    "Separator",
    ["Align Left", "Align Center", "Align Right"],
    ...(props.isFrappeDoc
      ? [
          "Separator",
          {
            label: "FontOptions",
            component: h(
              defineAsyncComponent(() => import("./components/FontFamily.vue")),
              {
                editor,
                font_size: props.settings.font_size || 15,
                font_family: props.settings.font_family || "inter",
              }
            ),
          },
          "FontColor",
          "Separator",
          {
            label: "Comment",
            icon: LucideMessageCircle,
            action: createNewComment,
            isActive: () => false,
          },
          "Image",
          "Video",
          "Iframe",
        ]
      : []),
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
  ])
)

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

// Util functions
const autorename = (bypass = false) => {
  const { $anchor } = editor.value.view.state.selection
  // Check if we're in the very first textblock
  if (!($anchor.index(0) === 1 && $anchor.depth === 1)) {
    // scroll down if in the last line
    if (
      $anchor.depth === 1 &&
      editor.value.state.doc.childCount - 1 === $anchor.index(0)
    ) {
      scrollParent.value.scroll(0, scrollParent.value.scrollHeight)
    }
    return
  }
  const implicitTitle = editor.value.state.doc.firstChild.textContent
    .replaceAll("#", "")
    .replaceAll("@", "")
    .trim()
  if (!props.entity.title.startsWith("Untitled Document") && !bypass) {
    // disable to improve ux
    // if (implicitTitle !== props.entity.title)
    //   toast({
    //     title: `Update title?`,
    //     buttons: [{ label: "Rename", onClick: () => autorename(true) }],
    //   })
    return
  }

  if (implicitTitle.length)
    rename.submit({
      entity_name: props.entity.name,
      new_title: implicitTitle,
    })
}

const getOrderedComments = (doc) => {
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
}

// Events
onKeyDown("p", (e) => {
  if (isModKey(e)) {
    e.preventDefault()
    if (editor.value) printDoc(editor.value.getHTML(), props.settings)
  }
})

emitter.on("printFile", () => {
  if (editor.value) printDoc(editor.value.getHTML(), props.settings)
})
emitter.on("create-version", (title) => {
  const snap = Y.snapshot(doc)
  emit("newVersion", Y.encodeSnapshot(snap), 0, title)
})

onMounted(() => {
  if (props.entity.mime_type === "frappe_doc") {
    const orderedComments = getOrderedComments(editor.value.state.doc)
    comments.value = props.entity.comments.toSorted((a, b) => {
      const pos1 = orderedComments.findIndex((k) => k.id === a.name)
      const pos2 = orderedComments.findIndex((k) => k.id === b.name)
      return pos1 - pos2
    })
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

onKeyDown("Enter", () => autorename())
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

const syncToWiki = async (wiki_space, group, entity_names) => {
  for (let k of entity_names) {
    const data = await createResource({
      url: "drive.api.wiki_integration.get_yjs_content",
      params: { entity_name: k },
    }).fetch()
    let pre_doc = new Y.Doc({ gc: true })
    Y.applyUpdate(pre_doc, toUint8Array(data))
    let obj = yDocToProsemirrorJSON(pre_doc, "default")
    let editor = new Editor({
      content: obj,
      extensions: textEditor.value.DEFAULT_EXTENSIONS,
    })
    await createResource({
      url: "drive.api.wiki_integration.sync_to_wiki_page",
      params: { entity_name: k, html: editor.getHTML(), wiki_space, group },
    }).fetch()
  }
}

window.run = () => syncToWiki(["uu9pbukv8s", "5fpvulc7so"])
const socket = inject("socket")
socket.on("sync_to_wiki", (data) => {
  for (let [title, pages] of Object.entries(data.groups)) {
    syncToWiki(data.space, title, pages)
  }
})
</script>
<style>
@import url("./styles/editor.css");
iframe {
  border: 1px solid var(--surface-gray-4) !important;
}

.h-full.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-gutter: stable;
}
</style>
