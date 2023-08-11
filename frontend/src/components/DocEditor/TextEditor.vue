<template>
  <div class="flex-col w-full overflow-y-auto">
    <div
      class="flex text-sm justify-center items-center text-gray-600 h-12 w-full">
      Created {{ $store.state.entityInfo.creation }}
    </div>
    <div class="flex w-full items-start justify-center">
      <editor-content
        class="flex w-full items-start justify-center"
        :editor="editor" />
    </div>
    <BubbleMenu
      v-on-outside-click="toggleCommentMenu"
      v-if="editor"
      :tippy-options="{ duration: 50, animation: 'shift-away' }"
      :should-show="shouldShow"
      :editor="editor">
      <div
        id="comment-box"
        v-if="
          showCommentMenu &&
          !editor.state.selection.empty &&
          !activeCommentsInstance.uuid
        "
        :editor="editor">
        <div
          class="absolute top-10 left-40 w-96 p-4 rounded-md border bg-white border-gray-100 shadow-lg">
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
  <DocMenuAndInfoBar :editor="editor" />
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
import Image from "./image-extension";
import Video from "./video-extension";
import Link from "@tiptap/extension-link";
import Typography from "@tiptap/extension-typography";
import TextStyle from "@tiptap/extension-text-style";
import Highlight from "@tiptap/extension-highlight";
import FontFamily from "@tiptap/extension-font-family";
import { FontSize } from "./font-size";
import { Color } from "@tiptap/extension-color";
import configureMention from "./mention";
import TextEditorFixedMenu from "./TextEditorFixedMenu.vue";
import TextEditorBubbleMenu from "./TextEditorBubbleMenu.vue";
import { detectMarkdown, markdownToHTML } from "../../utils/markdown";
import { DOMParser } from "prosemirror-model";
import MenuBar from "./MenuBar.vue";
import { Button, Input, onOutsideClickDirective } from "frappe-ui";
import { v4 as uuidv4 } from "uuid";
import { Comment } from "./comment";
import { LineHeight } from "./lineHeight";
import OuterCommentVue from "./OuterComment.vue";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import * as Y from "yjs";
import { WebrtcProvider } from "y-webrtc";
import { IndexeddbPersistence } from "y-indexeddb";
import { createEditorButton } from "./utils";
import DocMenuAndInfoBar from "./DocMenuAndInfoBar.vue";
import Menu from "./Menu.vue";

export default {
  name: "TextEditor",
  inheritAttrs: false,
  components: {
    EditorContent,
    BubbleMenu,
    TextEditorFixedMenu,
    TextEditorBubbleMenu,
    Menu,
    OuterCommentVue,
    MenuBar,
    DocMenuAndInfoBar,
  },
  directives: {
    onOutsideClick: onOutsideClickDirective,
  },
  provide() {
    return {
      editor: computed(() => this.editor),
    };
  },
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
      type: Object,
    },
    initialContent: {
      type: Object,
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
      buttons: [
        "Link",
        "Separator",
        "Bold",
        "Italic",
        "Underline",
        "Strikethrough",
        "Separator",
        "New Comment",
      ],
      provider: null,
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
  methods: {
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
        console.log(newVal);
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
            "prose prose-h1:font-bold prose-p:my-1 prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100",
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
    title() {
      this.$emit("update:title", this.title);
      this.$emit("saveTitle", this.title);
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
    const doc = new Y.Doc();
    Y.applyUpdate(doc, this.modelValue);
    // Tiny test
    // https://github.com/yjs/y-webrtc/blob/master/bin/server.js

    const indexeddbProvider = new IndexeddbPersistence(
      JSON.stringify(this.entityName),
      doc
    );

    const webrtcProvider = new WebrtcProvider(
      JSON.stringify(this.entityName),
      doc,
      { signaling: ["wss://network.arjunchoudhary.com"] }
    );
    this.provider = webrtcProvider;
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
      extensions: [
        StarterKit.configure({
          ...this.starterkitOptions,
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
        Link.configure({
          openOnClick: false,
        }),
        Comment.configure({
          isCommentModeOn: this.isCommentModeOn,
        }),
        Placeholder.configure({
          placeholder: "Start typing ...",
        }),
        Highlight.configure({
          multicolor: true,
        }),
        configureMention(this.mentions),
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
    this.emitter.on("toggleReadMode", () => {
      (this.isReadOnly = true), (this.tempEditable = false);
      this.isCommentModeOn = false;
    });
    this.emitter.on("toggleEditMode", () => {
      (this.isReadOnly = false), (this.tempEditable = true);
      this.isCommentModeOn = false;
    });
    this.emitter.on("toggleCommentMode", () => {
      (this.isReadOnly = false), (this.tempEditable = false);
      this.isCommentModeOn = true;
    });
    this.emitter.on("emitToggleCommentMenu", () => {
      this.showCommentMenu = !this.showCommentMenu;
    });
  },
  beforeUnmount() {
    this.editor.destroy();
    this.provider.destroy();
    this.provider = null;
    this.editor = null;
  },
};
</script>

<style>
.ProseMirror {
  outline: none;
  caret-color: theme("colors.blue.600");
  word-break: break-word;
  min-width: 75%;
  max-width: 75%;
  min-height: 90vh;
  -webkit-user-select: none;
  /* Safari */
  -ms-user-select: none;
  /* IE 10 and IE 11 */
  user-select: none;
  /* Standard syntax */
  padding: 1rem;
}

/* Firefox */
.ProseMirror-focused:focus-visible {
  outline: none;
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
</style>
