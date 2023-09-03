<template>
  <div class="flex-col w-full overflow-y-scroll">
    <div class="flex w-full items-start justify-center">
      <editor-content id="editor-capture" class="" :editor="editor" />
    </div>
    <BubbleMenu
      v-if="editor"
      v-on-outside-click="toggleCommentMenu"
      :tippy-options="{ duration: 50, animation: 'shift-away' }"
      :should-show="shouldShow"
      :editor="editor">
      <div
        v-if="
          showCommentMenu &&
          !editor.state.selection.empty &&
          !activeCommentsInstance.uuid
        "
        id="comment-box"
        :editor="editor">
        <div
          class="absolute top-10 left-0 w-96 p-4 rounded-md border bg-white border-gray-100 shadow-2xl">
          <textarea
            v-model="commentText"
            cols="50"
            rows="4"
            placeholder="Type your comment"
            style="resize: none"
            class="placeholder-gray-500 form-input block w-full mb-2"
            @keypress.enter.stop.prevent="() => setComment()" />
          <section class="flex justify-end gap-2">
            <Button @click="() => discardComment()">Discard</Button>
            <Button appearance="primary" @click="() => setComment()">
              Done
            </Button>
          </section>
        </div>
      </div>
      <Menu
        class="rounded-md border border-gray-100 shadow-lg"
        :buttons="bubbleMenuButtons" />
    </BubbleMenu>
  </div>
  <DocMenuAndInfoBar v-if="isWritable" :editor="editor" />
  <InfoSidebar v-else />
</template>

<script>
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
import TextStyle from "@tiptap/extension-text-style";
import Highlight from "@tiptap/extension-highlight";
import FontFamily from "@tiptap/extension-font-family";
import TaskItem from "@tiptap/extension-task-item";
import TaskList from "@tiptap/extension-task-list";
import { FontSize } from "./font-size";
import { Color } from "@tiptap/extension-color";
import configureMention from "./mention";
import { detectMarkdown, markdownToHTML } from "../../utils/markdown";
import { DOMParser } from "prosemirror-model";
import { onOutsideClickDirective } from "frappe-ui";
import { v4 as uuidv4 } from "uuid";
import { Comment } from "./comment";
import { LineHeight } from "./lineHeight";
import { Indent } from "./indent";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import * as Y from "yjs";
import { WebrtcProvider } from "y-webrtc";
import { IndexeddbPersistence } from "y-indexeddb";
import { createEditorButton } from "./utils";
import DocMenuAndInfoBar from "./DocMenuAndInfoBar.vue";
import Menu from "./Menu.vue";
import InfoSidebar from "../InfoSidebar.vue";

export default {
  name: "TextEditor",
  components: {
    EditorContent,
    BubbleMenu,
    Menu,
    DocMenuAndInfoBar,
    InfoSidebar,
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
  emits: ["update:modelValue"],
  data() {
    return {
      editor: null,
      buttons: ["Link", "Separator", "New Comment"],
      provider: null,
      localStore: null,
      tempEditable: true,
      isTextSelected: false,
      currentMode: "",
      showCommentMenu: false,
      commentText: "",
      isCommentModeOn: false,
      isReadOnly: false,
      activeCommentsInstance: {
        uuid: "",
        comments: [],
      },
      allComments: [],
    };
  },
  computed: {
    editable() {
      return this.isWritable && this.tempEditable;
    },
    bubbleMenuButtons() {
      return this.buttons.map(createEditorButton);
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
            "prose prose-h1:font-bold prose-p:my-1 prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100 border-gray-400 placeholder-gray-500 ",
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
    this.emitter.on("exportDocToPDF", () => {
      if (this.editor) {
        this.printEditorContent();
      }
    });
    const doc = new Y.Doc();
    Y.applyUpdate(doc, this.modelValue);
    // Tiny test
    // https://github.com/yjs/y-webrtc/blob/master/bin/server.js

    const indexeddbProvider = new IndexeddbPersistence(
      // Find a sane time to wipe IDB safely
      "fdoc" + JSON.stringify(this.entityName),
      doc
    );
    const webrtcProvider = new WebrtcProvider(
      "fdoc" + JSON.stringify(this.entityName),
      doc,
      { signaling: ["wss://network.arjunchoudhary.com"] }
    );
    this.provider = webrtcProvider;
    this.localStore = indexeddbProvider;
    let componentContext = this;
    this.editor = new Editor({
      editable: this.editable,
      editorProps: this.editorProps,
      onCreate() {
        componentContext.findCommentsAndStoreValues();
        componentContext.$emit("update:modelValue", Y.encodeStateAsUpdate(doc));
      },
      onUpdate() {
        componentContext.$emit("update:modelValue", Y.encodeStateAsUpdate(doc));
        componentContext.findCommentsAndStoreValues();
        componentContext.setCurrentComment();
      },
      onSelectionUpdate() {
        componentContext.setCurrentComment();
        componentContext.isTextSelected =
          !!componentContext.editor.state.selection.content().size;
      },
      // eslint-disable-next-line no-sparse-arrays
      extensions: [
        StarterKit.configure({
          history: false,
        }),
        Table.configure({
          resizable: true,
        }),
        FontFamily.configure({
          types: ["textStyle"],
        }),
        TextAlign.configure({
          types: ["heading", "paragraph"],
        }),
        ,
        Collaboration.configure({
          document: doc,
        }),
        CollaborationCursor.configure({
          provider: webrtcProvider,
          user: {
            name: this.currentUserName.toLowerCase(),
            avatar: this.currentUserImage,
            color: this.getRandomColor(),
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
        FontSize,
        Color,
        Image,
        Video,
      ],
    });
    this.emitter.on("emitToggleCommentMenu", () => {
      this.showCommentMenu = !this.showCommentMenu;
    });
  },
  beforeUnmount() {
    this.editor.destroy();
    this.localStore.clearData();
    this.provider.destroy();
    this.provider = null;
    this.editor = null;
  },
  methods: {
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
        this.editor.isActive("image") || this.editor.isActive("video");

      if (isMediaSelected) {
        return false;
      } else {
        return !(!view.hasFocus() || empty || isEmptyTextBlock);
      }
    },
    toggleCommentMenu() {
      if (this.showCommentMenu === true) {
        this.showCommentMenu = false;
      }
    },
    getRandomColor() {
      const list = [
        "#525252",
        "#775225",
        "#e11d48",
        "#20C1F4",
        "#2374D2",
        "#fbbf24",
        "#E39B4C",
        "#16a34a",
        "#EF7323",
        "#9333ea",
      ];
      return list[Math.floor(Math.random() * list.length)];
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
        this.showAddCommentSection = !this.editor.state.selection.empty;
        const parsedComment = JSON.parse(
          this.editor.getAttributes("comment").comment
        );
        parsedComment.comment =
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
};
</script>

<style>
.ProseMirror {
  outline: none;
  caret-color: theme("colors.blue.600");
  word-break: break-word;
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: none;
  padding: 0px;
}

/* Firefox */
.ProseMirror-focused:focus-visible {
  outline: none;
}

#editor-capture {
  background: white;
  padding: 4em;
  min-width: 21cm;
  max-width: 21cm;
  min-height: 29.7cm;
  max-height: 29.7cm;
}

/* print */
@page {
  size: a4;
  margin: 0;
}

span[data-comment] {
  background: rgb(228, 245, 233);
  border-bottom: 2px rgb(91, 185, 140) dashed;
  user-select: all;
  padding: 0 2px 0 2px;
  border-radius: 5px 5px 0px 0px;
}
.collaboration-cursor__caret {
  border-left: 1px solid #0d0d0d;
  border-right: 1px solid #0d0d0d;
  margin-left: -1px;
  margin-right: -1px;
  pointer-events: none;
  position: relative;
  word-break: normal;
}
/* Render the username above the caret */
.collaboration-cursor__label {
  border-radius: 1rem;
  color: #ffffffd0;
  font-size: 13px;
  font-style: normal;
  font-weight: 600;
  left: -1px;
  line-height: normal;
  padding: 0.2rem 0.5rem;
  position: absolute;
  top: -1.4em;
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
