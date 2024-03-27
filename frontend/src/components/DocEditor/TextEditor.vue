<template>
  <div class="flex-col w-full overflow-y-scroll" v-if="editor">
    <div class="flex w-full items-start justify-start lg:justify-center">
      <editor-content
        autocomplete="off"
        autocorrect="off"
        autocapitalize="off"
        spellcheck="true"
        id="editor-capture"
        :editor="editor" />
    </div>
    <BubbleMenu
      v-if="editor"
      v-show="!forceHideBubbleMenu"
      v-on-outside-click="toggleCommentMenu"
      :updateDelay="250"
      :tippy-options="{ animation: 'shift-away' }"
      :should-show="shouldShow"
      :editor="editor">
      <Menu
        class="rounded-md border border-gray-100 shadow-lg"
        :buttons="bubbleMenuButtons" />
    </BubbleMenu>
  </div>
  <DocMenuAndInfoBar :editor="editor" ref="MenuBar" />
  <FilePicker
    v-if="showFilePicker"
    v-model="showFilePicker"
    :suggestedTabIndex="1"
    @success="
      (val) => {
        pickedFile = val;
        showFilePicker = false;
        if (editor) {
          if (this.editable) {
            wordToHTML();
          }
        }
      }
    " />
  <NewComment
    v-if="showCommentMenu"
    :editor="editor"
    v-model="showCommentMenu"
    @success="() => (showCommentMenu = false)" />
</template>

<script>
import "tippy.js/animations/shift-away.css";
import { normalizeClass, computed } from "vue";
import {
  Editor,
  EditorContent,
  BubbleMenu,
  isTextSelection,
} from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Placeholder from "@tiptap/extension-placeholder";
import TextAlign from "@tiptap/extension-text-align";
import Table from "@tiptap/extension-table";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import TableRow from "@tiptap/extension-table-row";
import CharacterCount from "@tiptap/extension-character-count";
import Image from "./image-extension";
import Video from "./video-extension";
import Link from "@tiptap/extension-link";
import Typography from "@tiptap/extension-typography";
/* import TextStyle from "@tiptap/extension-text-style"; */
/* import Highlight from "@tiptap/extension-highlight";
 */ import FontFamily from "@tiptap/extension-font-family";
import TaskItem from "@tiptap/extension-task-item";
import TaskList from "@tiptap/extension-task-list";
import { FontSize } from "./font-size";
import { Highlight } from "./backgroundColor";
import { TextStyle } from "./text-style";
import { Color } from "@tiptap/extension-color";
import configureMention from "./mention";
import { detectMarkdown, markdownToHTML } from "../../utils/markdown";
import { DOMParser } from "prosemirror-model";
import { onOutsideClickDirective, Avatar } from "frappe-ui";
import { v4 as uuidv4 } from "uuid";
import { Comment } from "./comment";
import { LineHeight } from "./lineHeight";
import { Indent } from "./indent";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import * as Y from "yjs";
import { WebrtcProvider } from "y-webrtc";
import { createEditorButton } from "./utils";
import DocMenuAndInfoBar from "./DocMenuAndInfoBar.vue";
import Menu from "./Menu.vue";
import InfoSidebar from "../InfoSidebar.vue";
import { toast } from "@/utils/toasts.js";
import { PageBreak } from "./Pagebreak";
import { convertToHtml } from "mammoth";
import FilePicker from "@/components/FilePicker.vue";
import { ResizableMedia } from "./resizeableMedia";
import NewComment from "./NewComment.vue";
import { uploadDriveEntity } from "../../utils/chunkFileUpload";

export default {
  name: "TextEditor",
  components: {
    EditorContent,
    BubbleMenu,
    Menu,
    DocMenuAndInfoBar,
    InfoSidebar,
    toast,
    Avatar,
    FilePicker,
    ResizableMedia,
    NewComment,
  },
  directives: {
    onOutsideClick: onOutsideClickDirective,
  },
  provide() {
    return {
      editor: computed(() => this.editor),
    };
  },
  inheritAttrs: false,
  expose: ["editor"],
  props: {
    fixedMenu: {
      type: [Boolean, Array],
      default: false,
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
    modelValue: {
      type: Uint8Array,
      required: true,
      default: null,
    },
    placeholder: {
      type: String,
      default: "",
    },
    isWritable: {
      type: Boolean,
      default: false,
    },
    bubbleMenu: {
      type: [Boolean, Array],
      default: false,
    },
    bubbleMenuOptions: {
      type: Object,
      default: () => ({}),
    },
    mentions: {
      type: Array,
      default: () => [],
    },
  },
  emits: ["update:modelValue", "updateTitle", "saveDocument"],
  data() {
    return {
      editor: null,
      buttons: [],
      forceHideBubbleMenu: false,
      provider: null,
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
      allComments: [],
      originalTitle: this.entity.title,
    };
  },
  computed: {
    editable() {
      return this.isWritable && this.tempEditable;
    },
    bubbleMenuButtons() {
      if (this.entity.owner === "Me" || this.entity.write) {
        this.buttons = ["Link", "Separator", "New Comment"];
        return this.buttons.map(createEditorButton);
      } else if (this.entity.allow_comments) {
        this.buttons = ["New Comment"];
        return this.buttons.map(createEditorButton);
      }
    },
    currentUserName() {
      return this.$store.state.user.fullName;
    },
    currentUserImage() {
      return this.$store.state.user.imageURL;
    },
    editorProps() {
      return {
        attributes: {
          class: normalizeClass([
            "ProseMirror prose prose-sm leading-[21px] font-normal prose-h1:font-bold prose-p:my-1 prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100 border-gray-400 placeholder-gray-500 ",
          ]),
        },
        clipboardTextParser: (text, $context) => {
          if (!detectMarkdown(text)) return;
          if (
            !confirm(
              "Do you want to convert markdown content to HTML before pasting?"
            )
          )
            return;

          let dom = document.createElement("div");
          dom.innerHTML = markdownToHTML(text);
          let parser =
            this.editor.view.someProp("clipboardParser") ||
            this.editor.view.someProp("domParser") ||
            DOMParser.fromSchema(this.editor.schema);
          return parser.parseSlice(dom, {
            preserveWhitespace: true,
            context: $context,
          });
        },
      };
    },
  },
  watch: {
    activeCommentsInstance: {
      handler(newVal) {
        if (newVal) {
          // check if userid is available
          this.$store.commit(
            "setActiveCommentsInstance",
            JSON.stringify(newVal)
          );
        }
      },
      immediate: true,
    },
    allComments: {
      handler(newVal) {
        if (newVal) {
          this.$store.commit("setAllComments", JSON.stringify(newVal));
        }
      },
      immediate: true, // make this watch function is called when component created
    },
    editable(value) {
      this.editor.setEditable(value);
    },
    editorProps: {
      deep: true,
      attributes: {
        spellcheck: "false",
      },
      handler(value) {
        if (this.editor) {
          this.editor.setOptions({
            editorProps: value,
          });
        }
      },
    },
  },
  mounted() {
    if (window.matchMedia("(max-width: 1500px)").matches) {
      this.$store.commit("setIsSidebarExpanded", false);
    }
    this.emitter.on("exportDocToPDF", () => {
      if (this.editor) {
        this.printEditorContent();
      }
    });
    this.emitter.on("forceHideBubbleMenu", (val) => {
      if (this.editor) {
        this.forceHideBubbleMenu = val;
      }
    });
    this.emitter.on("importDocFromWord", () => {
      this.showFilePicker = true;
    });
    const doc = new Y.Doc();
    Y.applyUpdate(doc, this.modelValue);
    // Tiny test
    // https://github.com/yjs/y-webrtc/blob/master/bin/server.js

    /* const indexeddbProvider = new IndexeddbPersistence(
      // Find a sane time to wipe IDB safely
      "fdoc" + JSON.stringify(this.entityName),
      doc
    ); */
    const webrtcProvider = new WebrtcProvider(
      "fdoc" + JSON.stringify(this.entityName),
      doc,
      { signaling: ["wss://network.arjunchoudhary.com"] }
    );
    this.provider = webrtcProvider;
    this.awareness = this.provider.awareness.getStates();
    /* this.localStore = indexeddbProvider; */
    let componentContext = this;
    document.addEventListener("keydown", this.saveDoc);
    this.editor = new Editor({
      editable: this.editable,
      editorProps: this.editorProps,
      onCreate() {
        componentContext.findCommentsAndStoreValues();
        componentContext.$emit("update:modelValue", Y.encodeStateAsUpdate(doc));
        componentContext.updateConnectedUsers(componentContext.editor);
      },
      onUpdate() {
        componentContext.updateConnectedUsers(componentContext.editor);
        componentContext.$emit("update:modelValue", Y.encodeStateAsUpdate(doc));
        componentContext.findCommentsAndStoreValues();
        componentContext.setCurrentComment();
      },
      onSelectionUpdate() {
        componentContext.updateConnectedUsers(componentContext.editor);
        componentContext.setCurrentComment();
        componentContext.isTextSelected =
          !!componentContext.editor.state.selection.content().size;
      },
      // eslint-disable-next-line no-sparse-arrays
      extensions: [
        StarterKit.configure({
          history: false,
          heading: {
            levels: [1, 2, 3, 4],
            HTMLAttributes: {
              class: "not-prose leading-7",
            },
          },
          listItem: {
            HTMLAttributes: {
              class: "prose-list-item",
            },
          },
          /* codeBlock: {
            HTMLAttributes: {
              class: "my-5 px-4 py-2 text-sm text-black bg-gray-50 rounded border border-gray-200 leading-5 overflow-x-scroll",
            },
          }, */
          bulletList: {
            keepMarks: true,
            keepAttributes: false,
            HTMLAttributes: {
              class: "not-prose",
            },
          },
          orderedList: {
            keepMarks: true,
            keepAttributes: false,
            HTMLAttributes: {
              class: "not-prose",
            },
          },
        }),
        Table.configure({
          resizable: true,
        }),
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
          placeholder: "Start typing",
        }),
        Highlight.configure({
          multicolor: true,
        }),
        configureMention(this.mentions),
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
        TableRow,
        TableHeader,
        TableCell,
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
    });
    this.emitter.on("emitToggleCommentMenu", () => {
      if (this.editor?.isActive("comment") !== true) {
        this.showCommentMenu = !this.showCommentMenu;
      } else {
        this.$store.state.showInfo = true;
        this.$refs.MenuBar.tab = 1;
      }
    });
    setTimeout(() => {
      this.$emit("saveDocument");
    }, 10000);
  },
  updated() {
    let content = this.editor.state.doc.firstChild.textContent.slice(0, 35);
    if (this.originalTitle.includes("Untitled Document")) {
      if (content.length) {
        this.$store.state.entityInfo[0].title = content;
        this.$resources.rename.submit({
          entity_name: this.entityName,
          new_title: content,
        });
      } else {
        this.$store.state.entityInfo[0].title = this.originalTitle;
      }
    }
  },
  beforeUnmount() {
    //console.log(this.editor.getHTML());
    this.updateConnectedUsers(this.editor);
    document.removeEventListener("keydown", this.saveDoc);
    this.editor.destroy();
    /* this.localStore.clearData(); */
    this.provider.destroy();
    this.provider = null;
    this.editor = null;
  },
  methods: {
    evalTitle() {
      let content = this.editor.state.doc.firstChild.textContent.slice(0, 35);
      if (this.entity.title.includes("Untitled Document")) {
        this.$store.state.entityInfo[0]["title"] = content;
      }
      if (!content.length) {
        this.$store.state.entityInfo[0]["title"] = this.entity.title;
      }
    },
    updateConnectedUsers(editor) {
      this.$store.commit(
        "setConnectedUsers",
        editor.storage.collaborationCursor.users
      );
    },
    async wordToHTML() {
      let ctx = this;
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
        };
        const res = await fetch(
          `/api/method/drive.api.files.get_file_content?entity_name=${ctx.pickedFile.name}`,
          {
            method: "GET",
            headers,
          }
        );
        if (res.ok) {
          let blob = await res.arrayBuffer();

          convertToHtml({ arrayBuffer: blob })
            .then(function (result) {
              ctx.editor.commands.insertContent(result.value);
            })
            .catch(function (error) {
              console.error(error);
            });
          //.then((x) => console.log("docx: finished"));
        }
      } else {
        toast({
          title: "Not a valid DOCX file!",
          position: "bottom-right",
          icon: "alert-triangle",
          iconClasses: "text-red-500",
          timeout: 2,
        });
      }
    },
    saveDoc(e) {
      if (!(e.keyCode === 83 && (e.ctrlKey || e.metaKey))) {
        return;
      }
      e.preventDefault();
      this.$emit("saveDocument");
      toast({
        title: "Document saved",
        position: "bottom-right",
        timeout: 2,
      });
    },
    printHtml(dom) {
      const style = Array.from(document.querySelectorAll("style, link")).reduce(
        (str, style) => str + style.outerHTML,
        ""
      );
      const content = style + dom.outerHTML;

      const iframe = document.createElement("iframe");
      iframe.id = "el-tiptap-iframe";
      iframe.setAttribute(
        "style",
        "position: absolute; width: 0; height: 0; top: -10px; left: -10px;"
      );
      document.body.appendChild(iframe);

      const frameWindow = iframe.contentWindow;
      const doc =
        iframe.contentDocument ||
        (iframe.contentWindow && iframe.contentWindow.document);

      if (doc) {
        doc.open();
        doc.write(content);
        doc.close();
      }

      if (frameWindow) {
        iframe.onload = function () {
          try {
            setTimeout(() => {
              frameWindow.focus();
              try {
                if (!frameWindow.document.execCommand("print", false)) {
                  frameWindow.print();
                }
              } catch (e) {
                frameWindow.print();
              }
              frameWindow.close();
            }, 10);
          } catch (err) {
            console.error(err);
          }

          setTimeout(function () {
            document.body.removeChild(iframe);
          }, 100);
        };
      }
    },

    printEditorContent() {
      const editorContent = document.getElementById("editor-capture");
      if (editorContent) {
        this.printHtml(editorContent);
        return true;
      }
      return false;
    },
    shouldShow({ view, state, from, to }) {
      const { doc, selection } = state;
      const { empty } = selection;

      // Sometime check for `empty` is not enough.
      // Doubleclick an empty paragraph returns a node size of 2.
      // So we check also for an empty text size.
      const isEmptyTextBlock =
        !doc.textBetween(from, to).length && isTextSelection(state.selection);
      const isMediaSelected =
        this.editor.isActive("image") ||
        this.editor.isActive("video") ||
        this.editor.isActive("resizableMedia");
      if (isMediaSelected) {
        return false;
      } else if (this.buttons.length === 1) {
        return !(empty || isEmptyTextBlock);
      } else {
        return !(!view.hasFocus() || empty || isEmptyTextBlock);
      }
    },
    toggleCommentMenu() {
      if (this.showCommentMenu === true) {
        this.showCommentMenu = false;
      }
    },
    RndColor() {
      const max = 255;
      const min = 100;
      const range = max - min;
      const red = Math.floor(Math.random() * range) + min;
      const green = Math.floor(Math.random() * range) + min;
      const blue = Math.floor(Math.random() * range) + min;
      const redToHex = red.toString(16);
      const greenToHex = green.toString(16);
      const blueToHex = blue.toString(16);
      const rgbValue = "rgb(" + red + "," + green + "," + blue + ")";
      return "#" + redToHex + greenToHex + blueToHex;
    },
    discardComment() {
      this.commentText = "";
      this.isCommentModeOn = false;
    },
    getIsCommentModeOn() {
      return this.isCommentModeOn;
    },
    focusContent({ from, to }) {
      this.editor.chain().setTextSelection({ from, to }).run();
    },
    findCommentsAndStoreValues() {
      const tempComments = [];
      this.editor.state.doc.descendants((node, pos) => {
        const { marks } = node;
        marks.forEach((mark) => {
          if (mark.type.name === "comment") {
            const markComments = mark.attrs.comment;
            const jsonComments = markComments ? JSON.parse(markComments) : null;
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
              });
            }
          }
        });
      });
      return (this.allComments = tempComments);
    },
    setCurrentComment() {
      let newVal = this.editor.isActive("comment");
      if (newVal) {
        this.$store.state.showInfo = true;
        this.$refs.MenuBar.tab = 1;
        const parsedComment = JSON.parse(
          this.editor.getAttributes("comment").comment
        );
        parsedComment.comments =
          typeof parsedComment.comments === "string"
            ? JSON.parse(parsedComment.comments)
            : parsedComment.comments;
        this.activeCommentsInstance = parsedComment;
      } else {
        this.activeCommentsInstance = {};
      }
    },
    setComment(val) {
      const localVal = val || this.commentText;
      if (!localVal.trim().length) return;
      const currentSelectedComment = JSON.parse(
        JSON.stringify(this.activeCommentsInstance)
      );
      const commentsArray =
        typeof currentSelectedComment.comments === "string"
          ? JSON.parse(currentSelectedComment.comments)
          : currentSelectedComment.comments;
      if (commentsArray) {
        commentsArray.push({
          userName: this.currentUserName,
          userImage: this.currentUserImage,
          time: Date.now(),
          content: localVal,
        });
        const commentWithUuid = JSON.stringify({
          uuid: this.activeCommentsInstance.uuid || uuidv4(),
          comments: commentsArray,
        });
        this.editor.chain().setComment(commentWithUuid).run();
        this.commentText = "";
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
        });
        this.editor.chain().setComment(commentWithUuid).run();
        this.commentText = "";
      }
    },
  },
  resources: {
    rename() {
      return {
        url: "drive.api.files.passive_rename",
        debounce: 500,
      };
    },
  },
};
</script>

<style>
.ProseMirror {
  outline: none;
  caret-color: theme("colors.blue.600");
  word-break: break-word;
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: text;
  padding: 2em 1em;
  font-size: 14px;
  background: white;
  min-width: 21cm;
  max-width: 21cm;
  min-height: 29.7cm;
  max-height: 29.7cm;
}

/* Firefox */
.ProseMirror-focused:focus-visible {
  outline: none;
}

.ProseMirror h1 {
  font-size: 24px;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0em;
}

.ProseMirror h2 {
  font-size: 20px;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0em;
}

.ProseMirror h3 {
  font-size: 16px;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0em;
}

.ProseMirror blockquote {
  border-left: 2px solid lightgray;
  padding-left: 10px;
}

.ProseMirror strong {
  font-weight: 600;
}

.ProseMirror code,
pre {
  white-space: pre;
}

.ProseMirror hr {
  margin: 10px 0px;
}

.ProseMirror ul,
ol {
  list-style-type: revert;
  padding: revert;
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
  background: rgb(228, 245, 233);
  user-select: all;
  padding: 0 2px 0 2px;
  border-radius: 5px;
  cursor: pointer;
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
  border-radius: 10px;
  outline: none;
  cursor: pointer;
  margin-right: 5px;
}
.my-task-item input[type="checkbox"]:hover {
  outline: none;
  background-color: #0d0d0d;
}
.my-task-item input[type="checkbox"]:focus {
  outline: none;
  background-color: #0d0d0d;
}
.my-task-item input[type="checkbox"]:active {
  outline: none;
  background-color: #0d0d0d;
}
.my-task-item input[type="checkbox"]:checked {
  outline: none;
  background-color: #0d0d0d;
}
</style>
