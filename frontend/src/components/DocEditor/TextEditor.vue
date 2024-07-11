<template>
  <div v-if="editor && initComplete" class="flex-col w-full overflow-y-auto">
    <div
      :class="[
        settings.docFont,
        settings.docSize ? 'text-[15px]' : 'text-[17px]',
        settings.docWidth
          ? 'sm:min-w-[75vw] sm:max-w-[75vw]'
          : 'sm:min-w-[21cm] sm:max-w-[21cm]',
      ]"
      class="flex sm:w-full items-start justify-start lg:justify-center mx-auto"
    >
      <editor-content
        id="editor-capture"
        class="min-w-full"
        autocomplete="true"
        autocorrect="true"
        autocapitalize="true"
        spellcheck="true"
        :editor="editor"
        @keydown.enter.passive="handleEnterKey"
      />
    </div>
    <TableBubbleMenu v-if="isWritable" :editor="editor" />
    <BubbleMenu
      v-if="editor"
      v-show="!forceHideBubbleMenu"
      plugin-key="main"
      :should-show="shouldShow"
      :editor="editor"
    >
      <Menu :buttons="bubbleMenuButtons" />
    </BubbleMenu>
  </div>
  <DocMenuAndInfoBar
    v-if="editor && initComplete"
    ref="MenuBar"
    :editor="editor"
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
</template>

<script>
import "tippy.js/animations/shift-away.css"
import { normalizeClass, computed } from "vue"
import { Editor, EditorContent, BubbleMenu } from "@tiptap/vue-3"
import { Table } from "./Table"
import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import Placeholder from "@tiptap/extension-placeholder"
import TextAlign from "@tiptap/extension-text-align"
import CharacterCount from "@tiptap/extension-character-count"
import Link from "@tiptap/extension-link"
import Typography from "@tiptap/extension-typography"
import TableBubbleMenu from "./Table/menus/TableBubbleMenu.vue"
import FontFamily from "@tiptap/extension-font-family"
import TaskItem from "@tiptap/extension-task-item"
import TaskList from "@tiptap/extension-task-list"
import { FontSize } from "./font-size"
import { Highlight } from "./backgroundColor"
import { TextStyle } from "./text-style"
import { Color } from "@tiptap/extension-color"
import { detectMarkdown, markdownToHTML } from "../../utils/markdown"
import { DOMParser } from "prosemirror-model"
import { onOutsideClickDirective } from "frappe-ui"
import { v4 as uuidv4 } from "uuid"
import { Comment } from "./comment"
import { LineHeight } from "./lineHeight"
import { Indent } from "./indent"
import Collaboration from "@tiptap/extension-collaboration"
import CollaborationCursor from "@tiptap/extension-collaboration-cursor"
import * as Y from "yjs"
import { WebrtcProvider } from "y-webrtc"
import { IndexeddbPersistence } from "y-indexeddb"
import { createEditorButton } from "./utils"
import DocMenuAndInfoBar from "./DocMenuAndInfoBar.vue"
import Menu from "./Menu.vue"
import { toast } from "@/utils/toasts.js"
import { PageBreak } from "./Pagebreak"
import FilePicker from "@/components/FilePicker.vue"
import { ResizableMedia } from "./resizeableMedia"
import { uploadDriveEntity } from "../../utils/chunkFileUpload"
import configureMention from "./Mention/mention"

import Commands from "./Suggestion/suggestionExtension"
import suggestion from "./Suggestion/suggestion"

export default {
  name: "TextEditor",
  components: {
    EditorContent,
    BubbleMenu,
    Menu,
    DocMenuAndInfoBar,
    FilePicker,
    TableBubbleMenu,
  },
  directives: {
    onOutsideClick: onOutsideClickDirective,
  },
  provide() {
    return {
      editor: computed(() => this.editor),
    }
  },
  inheritAttrs: false,
  expose: ["editor"],
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
      allComments: [],
      isNewDocument: this.entity.title.includes("Untitled Document"),
    }
  },
  computed: {
    editable() {
      return this.isWritable && this.tempEditable
    },
    bubbleMenuButtons() {
      if (this.entity.owner === "You" || this.entity.write) {
        let buttons = [
          "Bold",
          "Italic",
          "Underline",
          "Strikethrough",
          "Code",
          "Separator",
          "Link",
          "Separator",
          "Comment",
        ]
        return buttons.map(createEditorButton)
      } else if (this.entity.allow_comments) {
        let buttons = ["Comment"]
        return buttons.map(createEditorButton)
      }
      return []
    },
    currentUserName() {
      return this.$store.state.user.fullName
    },
    currentUserImage() {
      return this.$store.state.user.imageURL
    },
  },
  watch: {
    isNewDocument: {
      handler(val) {
        if (val) {
          this.$store.state.passiveRename = true
        } else {
          this.$store.state.passiveRename = false
        }
      },
      immediate: true,
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
    if (window.matchMedia("(max-width: 1500px)").matches) {
      this.$store.commit("setIsSidebarExpanded", false)
    }
    this.emitter.on("exportDocToPDF", () => {
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
    const doc = new Y.Doc()
    const ymap = doc.getMap("docinfo")
    ymap.set("lastsaved", this.lastSaved)
    this.document = doc

    const indexeddbProvider = new IndexeddbPersistence(
      "fdoc-" + JSON.stringify(this.entityName),
      doc
    )
    indexeddbProvider.on("synced", () => {
      this.initComplete = true
    })
    Y.applyUpdate(doc, this.yjsContent)
    const webrtcProvider = new WebrtcProvider(
      "fdoc-" + JSON.stringify(this.entityName),
      doc,
      { signaling: ["wss://network.arjunchoudhary.com"] }
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
      autofocus: true,
      editorProps: {
        attributes: {
          class: normalizeClass([
            `ProseMirror prose prose-sm prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100 rounded-b-lg max-w-[unset] pb-[50vh] md:px-[70px]`,
          ]),
        },
        clipboardTextParser: (text, $context) => {
          if (!detectMarkdown(text)) return
          if (
            !confirm(
              "Do you want to convert markdown content to HTML before pasting?"
            )
          )
            return

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
        componentContext.findCommentsAndStoreValues()
        componentContext.updateConnectedUsers(componentContext.editor)
      },
      onUpdate() {
        componentContext.updateConnectedUsers(componentContext.editor)
        componentContext.findCommentsAndStoreValues()
        componentContext.setCurrentComment()
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
      },
      onSelectionUpdate() {
        componentContext.updateConnectedUsers(componentContext.editor)
        componentContext.setCurrentComment()
        componentContext.isTextSelected =
          !!componentContext.editor.state.selection.content().size
      },
      // eslint-disable-next-line no-sparse-arrays
      extensions: [
        StarterKit.configure({
          history: false,
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
              class:
                "not-prose my-5 px-4 py-2 text-[0.9em] font-mono text-black bg-gray-50 rounded border border-gray-300 overflow-x-auto",
            },
          },
          blockquote: {
            HTMLAttributes: {
              class:
                "prose-quoteless text-black border-l-2 pl-2 border-gray-400 text-[0.9em]",
            },
          },
          code: {
            HTMLAttributes: {
              class:
                "not-prose px-px font-mono bg-gray-50 text-[0.85em] rounded-sm border border-gray-300",
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
        Comment.configure({
          isCommentModeOn: this.isCommentModeOn,
        }),
        Placeholder.configure({
          placeholder: "Press / for commands",
        }),
        Highlight.configure({
          multicolor: true,
        }),
        configureMention(this.userList),
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
          uploadFn: (file) => uploadDriveEntity(file, this.entityName),
        }),
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
  },
  updated() {
    if (this.isNewDocument) {
      this.evalImplicitTitle()
    }
  },
  beforeUnmount() {
    this.updateConnectedUsers(this.editor)
    this.$store.state.passiveRename = false
    document.removeEventListener("keydown", this.saveDoc)
    this.editor.destroy()
    this.document.destroy()
    this.provider.disconnect()
    this.provider.destroy()
    this.provider = null
    this.editor = null
  },
  methods: {
    handleEnterKey() {
      if (this.$store.state.passiveRename) {
        if (!this.implicitTitle.length) return
        this.isNewDocument = false
      }
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
          //.then((x) => console.log("docx: finished"));
        }
      } else {
        toast({
          title: "Not a valid DOCX file!",
          position: "bottom-right",
          icon: "alert-triangle",
          iconClasses: "text-red-500",
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
        position: "bottom-right",
        timeout: 2,
      })
    },
    printHtml(dom) {
      const style = Array.from(document.querySelectorAll("style, link")).reduce(
        (str, style) => str + style.outerHTML,
        ""
      )
      const content = style + dom.outerHTML

      const iframe = document.createElement("iframe")
      iframe.id = "el-tiptap-iframe"
      iframe.setAttribute(
        "style",
        "position: absolute; width: 0; height: 0; top: -10px; left: -10px;"
      )
      document.body.appendChild(iframe)

      const frameWindow = iframe.contentWindow
      const doc =
        iframe.contentDocument ||
        (iframe.contentWindow && iframe.contentWindow.document)

      if (doc) {
        doc.open()
        doc.write(content)
        doc.close()
      }

      if (frameWindow) {
        iframe.onload = function () {
          try {
            setTimeout(() => {
              frameWindow.focus()
              try {
                if (!frameWindow.document.execCommand("print", false)) {
                  frameWindow.print()
                }
              } catch (e) {
                frameWindow.print()
              }
              frameWindow.close()
            }, 10)
          } catch (err) {
            console.error(err)
          }

          setTimeout(function () {
            document.body.removeChild(iframe)
          }, 100)
        }
      }
    },
    printEditorContent() {
      const editorContent = document.getElementById("editor-capture")
      if (editorContent) {
        this.printHtml(editorContent)
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
      this.implicitTitle = this.editor.state.doc.textContent.trim().slice(0, 35)
      this.implicitTitle = this.implicitTitle.trim()
      if (this.implicitTitle.charAt(0) === "@") {
        return
      }
      if (this.implicitTitle.length && this.$store.state.passiveRename) {
        this.$store.state.entityInfo[0].title = this.implicitTitle
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
        url: "drive.api.files.passive_rename",
        debounce: 500,
      }
    },
  },
}
</script>

<style>
.ProseMirror {
  outline: none;
  caret-color: theme("colors.blue.600");
  word-break: break-word;
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: text;
  padding: 4em 1em;
  background: white;
}

/* 640 is sm from espresso design */
@media only screen and (max-width: 640px) {
  .ProseMirror {
    display: block;
    max-width: 100%;
    min-width: 100%;
  }
}

.ProseMirror a {
  text-decoration: underline;
}

/* Firefox */
.ProseMirror-focused:focus-visible {
  outline: none;
}

@page {
  size: a4;
  margin: 4em;
}
/* 
  Omit the page break div from printing added from `PageBreak.ts`
*/
@media print {
  #page-break-div {
    border: none !important;
    margin: none !important;
  }
}

span[data-comment] {
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

/* Check list */
.my-task-item {
  display: flex;
}
.my-task-item input {
  border-radius: 4px;
  outline: 0;
  margin-right: 10px;
}
.my-task-item input[type="checkbox"]:hover {
  outline: 0;
  background-color: #d6d6d6;
  cursor: pointer;
  transition: background 0.2s ease, border 0.2s ease;
}
.my-task-item input[type="checkbox"]:focus {
  outline: 0;
  background-color: #5b5b5b;
}
.my-task-item input[type="checkbox"]:active {
  outline: 0;
  background-color: #5b5b5b;
}
.my-task-item input[type="checkbox"]:checked {
  outline: 0;
  background-color: #000000;
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
