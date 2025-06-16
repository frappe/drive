<template>
  <div
    v-if="editor && initComplete"
    class="flex-col w-full overflow-y-auto"
  >
    <div
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
        @keydown.enter.passive="handleEnterKey"
      />
    </div>
    <TableBubbleMenu
      v-if="isWritable"
      :editor="editor"
    />
    <BubbleMenu
      v-if="editor"
      v-show="!forceHideBubbleMenu"
      plugin-key="main"
      :should-show="shouldShow"
      :editor="editor"
      :update-delay="0"
      :tippy-options="{
        appendTo: 'parent',
        placement: 'top',
        offset: [0, 5],
        maxWidth: 500,
      }"
    >
      <Menu :buttons="bubbleMenuButtons" />
    </BubbleMenu>
  </div>
  <DocMenuAndInfoBar
    v-if="editor && initComplete"
    ref="MenuBar"
    v-model:all-annotations="allAnnotations"
    v-model:active-annotation="activeAnnotation"
    :editor="editor"
    :versions="versions"
    :settings="settings"
  />
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
</template>

<script>
import FilePicker from "@/components/FilePicker.vue"
import { toast } from "@/utils/toasts.js"
import Link from "@tiptap/extension-link"
import TaskItem from "@tiptap/extension-task-item"
import TaskList from "@tiptap/extension-task-list"
import Typography from "@tiptap/extension-typography"
import StarterKit from "@tiptap/starter-kit"
import { BubbleMenu, Editor, EditorContent } from "@tiptap/vue-3"
import { onOutsideClickDirective } from "frappe-ui"
import { DOMParser } from "prosemirror-model"
import { v4 as uuidv4 } from "uuid"
import { computed, normalizeClass } from "vue"
import { IndexeddbPersistence } from "y-indexeddb"
import { WebrtcProvider } from "y-webrtc"
import * as Y from "yjs"
import { uploadDriveEntity } from "@/utils/chunkFileUpload"
import { detectMarkdown, markdownToHTML } from "@/utils/markdown"
import DocMenuAndInfoBar from "./components/DocMenuAndInfoBar.vue"
import configureMention from "./extensions/mention/mention"
import Menu from "./components/Menu.vue"
import { Table } from "./extensions/table"
import TableBubbleMenu from "./components/TableBubbleMenu.vue"
import { PageBreak } from "./extensions/Pagebreak"
import { Highlight } from "./extensions/backgroundColor"
import { CharacterCount } from "./extensions/character-count"
import { Collaboration } from "./extensions/collaboration"
import { CollaborationCursor } from "./extensions/collaborationCursor"
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
import { createEditorButton } from "./utils"
import { Annotation } from "./extensions/AnnotationExtension/annotation"
import suggestion from "./extensions/suggestion/suggestion"
import Commands from "./extensions/suggestion/suggestionExtension"
import SnapshotPreviewDialog from "./components/SnapshotPreviewDialog.vue"
import { DiffMarkExtension } from "./extensions/createDiffMark"
import { printDoc } from "@/utils/files"

export default {
  name: "TextEditor",
  components: {
    EditorContent,
    BubbleMenu,
    Menu,
    DocMenuAndInfoBar,
    FilePicker,
    TableBubbleMenu,
    SnapshotPreviewDialog,
  },
  directives: {
    onOutsideClick: onOutsideClickDirective,
  },
  provide() {
    return {
      editor: computed(() => this.editor),
      document: computed(() => this.document),
      versions: computed(() => this.versions),
    }
  },
  inheritAttrs: false,
  //expose: ["editor", "versions"],
  props: {
    settings: {
      type: Object,
      default: null,
    },
    entityName: {
      default: "",
      type: String,
      required: false,
    },
    entity: {
      default: null,
      type: Object,
      required: false,
    },
    documentName: {
      default: "",
      type: String,
      required: false,
    },
    yjsContent: {
      type: Uint8Array,
      required: true,
      default: null,
    },
    lastSaved: {
      type: Number,
      required: true,
    },
    rawContent: {
      type: String,
      required: true,
      default: null,
    },
    isWritable: {
      type: Boolean,
      default: false,
    },
    userList: {
      type: Object,
      required: true,
      default: null,
    },
  },
  emits: [
    "update:yjsContent",
    "updateTitle",
    "saveDocument",
    "mentionedUsers",
    "update:rawContent",
    "update:lastSaved",
  ],
  data() {
    return {
      docWidth: this.settings.docWidth,
      docSize: this.settings.docSize,
      docFont: this.settings.docFont,
      editor: null,
      defaultFont: "font-sans",
      buttons: [],
      forceHideBubbleMenu: false,
      synced: false,
      peercount: 0,
      initComplete: true,
      provider: null,
      document: null,
      awareness: null,
      connectedUsers: null,
      localStore: null,
      tempEditable: true,
      isTextSelected: false,
      currentMode: "",
      showCommentMenu: false,
      commentText: "",
      isCommentModeOn: true,
      isReadOnly: false,
      showFilePicker: false,
      pickedFile: null,
      activeCommentsInstance: {
        uuid: "",
        comments: [],
      },
      implicitTitle: "",
      allAnnotations: [],
      allComments: [],
      activeAnnotation: "",
      activeAnchorAnnotations: null,
      isNewDocument: this.entity.title.includes("Untitled Document"),
      versions: [],
      selectedSnapshot: null,
      snapShotDialog: false,
    }
  },
  computed: {
    editable() {
      return this.isWritable && this.tempEditable
    },
    bubbleMenuButtons() {
      let buttons = []
      if (this.entity.write) {
        buttons.push(
          "Bold",
          "Italic",
          "Underline",
          "Strikethrough",
          "Code",
          "Separator",
          "Link"
        )
      }
      if (this.entity.owner == "You") {
        buttons.push("Separator", "NewAnnotation")
      } else if (this.entity.comment) {
        buttons.push("NewAnnotation")
      }
      return buttons.map(createEditorButton)
    },
    currentUserName() {
      return this.$store.state.user.fullName
    },
    currentUserImage() {
      return this.$store.state.user.imageURL
    },
  },
  watch: {
    activeAnchorAnnotations: {
      handler(newVal) {
        if (newVal) {
          // unexpected case??
          let yArray = this.document.getArray("docAnnotations")
          // Toggle visibility if it's not visible in the document anymore
          yArray.forEach((item) => {
            if (newVal.has(item.get("id"))) {
              item.set("anchor", 1)
            } else {
              item.set("anchor", 0)
            }
          })
        }
      },
    },
    lastSaved(newVal) {
      const ymap = this.document.getMap("docinfo")
      const lastSaved = ymap.get("lastsaved")
      if (newVal > lastSaved) {
        ymap.set("lastsaved", newVal)
      }
    },
    settings(newVal) {
      switch (newVal.toLowerCase()) {
        case "sans":
          this.defaultFont = "font-['Nunito']"
          break
        case "serif":
          this.defaultFont = "font-['Lora']"
          break
        case "round":
          this.defaultFont = "font-['Nunito']"
          break
        case "mono":
          this.defaultFont = "font-['Geist-Mono']"
          break
        default:
          this.defaultFont = "font-['InterVar']"
      }
    },
    activeCommentsInstance: {
      handler(newVal) {
        if (newVal) {
          // check if userid is available
          this.$store.commit(
            "setActiveCommentsInstance",
            JSON.stringify(newVal)
          )
        }
      },
      immediate: true,
    },
    allComments: {
      handler(newVal) {
        if (newVal) {
          this.$store.commit("setAllComments", JSON.stringify(newVal))
        }
      },
      immediate: true, // make this watch function is called when component created
    },
    editable(value) {
      this.editor.setEditable(value)
    },
  },
  mounted() {
    this.emitter.on("printFile", () => {
      if (this.editor) {
        this.printEditorContent()
      }
    })
    this.emitter.on("forceHideBubbleMenu", (val) => {
      if (this.editor) {
        this.forceHideBubbleMenu = val
      }
    })
    this.emitter.on("importDocFromWord", () => {
      this.showFilePicker = true
    })
    const doc = new Y.Doc({ gc: false })
    const ymap = doc.getMap("docinfo")
    ymap.set("lastsaved", this.lastSaved)
    this.document = doc

    const indexeddbProvider = new IndexeddbPersistence(
      "fdoc-" + JSON.stringify(this.entityName),
      doc
    )
    Y.applyUpdate(doc, this.yjsContent)
    const webrtcProvider = new WebrtcProvider(
      "fdoc-" + JSON.stringify(this.entityName),
      doc
    )
    ymap.observe(() => {
      this.$emit("update:lastSaved", ymap.get("lastsaved"))
    })
    this.provider = webrtcProvider
    this.awareness = this.provider.awareness
    this.localStore = indexeddbProvider
    let componentContext = this
    document.addEventListener("keydown", this.saveDoc)
    this.editor = new Editor({
      editable: this.editable,
      autofocus: "start",
      editorProps: {
        attributes: {
          class: normalizeClass([`prose prose-sm`]),
        },
        clipboardTextParser: (text, $context) => {
          if (!detectMarkdown(text)) return
          let dom = document.createElement("div")
          dom.innerHTML = markdownToHTML(text)
          let parser =
            this.editor.view.someProp("clipboardParser") ||
            this.editor.view.someProp("domParser") ||
            DOMParser.fromSchema(this.editor.schema)
          return parser.parseSlice(dom, {
            preserveWhitespace: true,
            context: $context,
          })
        },
      },
      onCreate() {
        //componentContext.findCommentsAndStoreValues()
        //componentContext.updateConnectedUsers(componentContext.editor)
      },
      // evaluate document version
      onUpdate() {
        //componentContext.updateConnectedUsers(componentContext.editor)
        //componentContext.findCommentsAndStoreValues()
        componentContext.setCurrentComment()
        if (
          componentContext.$props.rawContent ===
          componentContext.editor.getHTML()
        )
          return
        componentContext.$emit(
          "update:rawContent",
          componentContext.editor.getHTML()
        )
        componentContext.$emit(
          "mentionedUsers",
          componentContext.parseMentions(componentContext.editor.getJSON())
        )
        componentContext.$emit(
          "update:yjsContent",
          Y.encodeStateAsUpdate(componentContext.document)
        )
        componentContext.updateAnnotationStatus()
      },
      onSelectionUpdate() {
        //componentContext.updateConnectedUsers(componentContext.editor)
        //componentContext.setCurrentComment()
        //componentContext.isTextSelected =
        //  !!componentContext.editor.state.selection.content().size
      },
      // eslint-disable-next-line no-sparse-arrays
      extensions: [
        StarterKit.configure({
          history: false,
          paragraph: {
            HTMLAttributes: {
              class: this.entity.version == 0 ? "legacy" : "",
            },
          },
          heading: {
            levels: [1, 2, 3, 4, 5],
          },
          listItem: {
            HTMLAttributes: {
              class: "prose-list-item",
            },
          },
          codeBlock: {
            HTMLAttributes: {
              spellcheck: false,
            },
          },
          blockquote: {
            HTMLAttributes: {},
          },
          code: {
            HTMLAttributes: {},
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
        Commands.configure({
          suggestion,
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
        Annotation.configure({
          onAnnotationClicked: (ID) => {
            componentContext.setAndFocusCurrentAnnotation(ID)
          },
          onAnnotationActivated: (ID) => {
            //this.activeAnnotation = ID
            if (ID) setTimeout(() => componentContext.setCurrentAnnotation(ID))
          },
          HTMLAttributes: {
            //class: 'cursor-pointer annotation  annotation-number'
            //class: 'cursor-pointer bg-amber-300 bg-opacity-20 border-b-2 border-yellow-300 pb-[1px]'
            class: "cursor-pointer annotation",
          },
        }),
        Collaboration.configure({
          document: doc,
        }),
        CollaborationCursor.configure({
          provider: webrtcProvider,
          user: {
            name: this.currentUserName,
            avatar: this.currentUserImage,
            color: this.RndColor(),
          },
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
        configureMention(this.userList),
        TaskList.configure({
          HTMLAttributes: {},
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
          uploadFn: (file) =>
            uploadDriveEntity(file, this.entity.team, this.entityName),
        }),
        DiffMarkExtension,
      ],
    })
    this.emitter.on("emitToggleCommentMenu", () => {
      if (this.editor?.isActive("comment") !== true) {
        this.showCommentMenu = !this.showCommentMenu
      } else {
        this.$store.state.showInfo = true
        this.$refs.MenuBar.tab = 5
      }
    })
    window.addEventListener("offline", () => {
      this.provider.disconnect()
      this.synced = false
      this.connected = false
      this.peercount = 0
    })
    window.addEventListener("online", () => {
      this.provider.connect()
    })
    this.localStore.on("synced", () => {
      this.initComplete = true
    })
    this.provider.on("status", (e) => {
      this.connected = e.connected
    })
    this.provider.on("peers", (e) => {
      this.peercount = e.webrtcPeers.length
    })
    this.awareness.on("update", () => {
      this.$store.commit(
        "setConnectedUsers",
        this.editor?.storage.collaborationCursor.users
      )
    })
    this.provider.on("synced", (e) => {
      this.synced = e.synced
    })
    this.$realtime.doc_subscribe("Drive File", this.entityName)
    this.$realtime.doc_open("Drive File", this.entityName)
    this.$realtime.on("document_version_change_recv", (data) => {
      const { author, author_image, author_id } = data
      if (author_id === this.$realtime.socket.id) {
        toast({
          title: "You changed the document version",
          position: "bottom-right",
          timeout: 2,
        })
        return
      }
      toast({
        title: `Document version changed`,
        position: "bottom-right",
        avatarURL: author_image,
        avatarLabel: author,
        timeout: 2,
      })
    })
  },
  beforeUnmount() {
    this.emitter.off("printFile")
    this.emitter.off("forceHideBubbleMenu")
    this.emitter.off("importDocFromWord")
    this.$realtime.off("document_version_change_recv")
    this.$realtime.doc_close("Drive File", this.entityName)
    this.$realtime.doc_unsubscribe("Drive File", this.entityName)
    this.updateConnectedUsers(this.editor)
    document.removeEventListener("keydown", this.saveDoc)
    this.editor.destroy()
    this.document.destroy()
    this.provider.disconnect()
    this.provider.destroy()
    this.provider = null
    this.editor = null
  },
  methods: {
    updateAnnotationStatus() {
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
    },
    handleEnterKey() {
      if (this.entity.title === "Untitled Document") this.evalImplicitTitle()
    },
    updateConnectedUsers(editor) {
      this.$store.commit(
        "setConnectedUsers",
        editor.storage.collaborationCursor.users
      )
    },
    async wordToHTML() {
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
    },
    saveDoc(e) {
      if (!(e.keyCode === 83 && (e.ctrlKey || e.metaKey))) {
        return
      }
      e.preventDefault()
      this.$emit("update:rawContent", this.editor.getHTML())
      this.$emit("update:yjsContent", Y.encodeStateAsUpdate(this.document))
      this.$emit("mentionedUsers", this.parseMentions(this.editor.getJSON()))
      if (this.synced || this.peercount === 0) {
        this.$emit("saveDocument")
      }
      toast({
        title: "Document saved",
      })
    },
    printEditorContent() {
      const html = this.editor.getHTML()
      if (html) {
        printDoc(html)
        return true
      }
      return false
    },
    shouldShow: ({ state }) => {
      const { from, to } = state.selection
      // Check if the selection is within a text node
      const node = state.doc.nodeAt(from)
      if (node && node.type.name === "text") {
        // Ensure the selection is not empty
        return from !== to
      }
      return false // Hide the menu if the selection is outside a text node
    },
    RndColor() {
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
    },
    discardComment() {
      this.commentText = ""
      this.isCommentModeOn = false
    },
    getIsCommentModeOn() {
      return this.isCommentModeOn
    },
    focusContent({ from, to }) {
      this.editor.chain().setTextSelection({ from, to }).run()
    },
    findCommentsAndStoreValues() {
      const tempComments = []
      this.editor.state.doc.descendants((node, pos) => {
        const { marks } = node
        marks.forEach((mark) => {
          if (mark.type.name === "comment") {
            const markComments = mark.attrs.comment
            const jsonComments = markComments ? JSON.parse(markComments) : null
            if (
              jsonComments !== null &&
              !tempComments.find(
                (el) => el.jsonComments.uuid === jsonComments.uuid
              )
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
    },
    setCurrentAnnotation() {
      let newVal = this.editor.isActive("annotation")
      const sideBarState =
        this.$store.state.showInfo && this.$refs.MenuBar.tab == 5
      if (newVal && sideBarState) {
        this.activeAnnotation =
          this.editor.getAttributes("annotation").annotationID
      }
    },
    //Click
    setAndFocusCurrentAnnotation() {
      let newVal = this.editor.isActive("annotation")
      if (newVal) {
        this.$store.state.showInfo = true
        this.$refs.MenuBar.tab = 5
        this.activeAnnotation =
          this.editor.getAttributes("annotation").annotationID
      }
    },
    setCurrentComment() {
      let newVal = this.editor.isActive("comment")
      if (newVal) {
        this.$store.state.showInfo = true
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
    },
    setComment(val) {
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
          userName: this.currentUserName,
          userImage: this.currentUserImage,
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
              userName: this.currentUserName,
              userImage: this.currentUserImage,
              time: Date.now(),
              content: localVal,
            },
          ],
        })
        this.editor.chain().setComment(commentWithUuid).run()
        this.commentText = ""
      }
    },
    parseMentions(data) {
      const tempMentions = (data.content || []).flatMap(this.parseMentions)
      if (data.type === "mention") {
        tempMentions.push({
          id: data.attrs.id,
          author: data.attrs.author,
          type: data.attrs.type,
        })
      }
      const uniqueMentions = [
        ...new Set(tempMentions.map((item) => item.id)),
      ].map((id) => tempMentions.find((item) => item.id === id))
      return uniqueMentions
    },
    evalImplicitTitle() {
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
        this.$store.state.activeEntity.title = this.implicitTitle
        this.$resources.rename.submit({
          entity_name: this.entityName,
          new_title: this.implicitTitle,
        })
      }
    },
  },
  resources: {
    rename() {
      return {
        url: "drive.api.files.call_controller_method",
        makeParams: (params) => ({
          method: "rename",
          ...params,
        }),
        onSuccess: () => {
          this.$store.state.breadcrumbs[
            this.$store.state.breadcrumbs.length - 1
          ].label = this.implicitTitle
        },
        debounce: 500,
      }
    },
  },
}
</script>

<style>
@import url("./editor.css");

span[data-annotation-id] {
  background: rgba(255, 215, 0, 0.15);
  border-bottom: 2px solid rgb(255, 210, 0);
  user-select: text;
  padding: 2px;
}

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
