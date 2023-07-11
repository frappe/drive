<template>
  <div class="sticky top-0 z-10">
    <div v-if="editor && editable" class="w-full">
      <!-- <MenuBar 
          :entityName="entityName" 
          :currentMode="currentMode" 
          @toggle-comment-mode="() => this.toggleCommentMode()" 
          @toggle-edit-mode="() => this.toggleEditMode()" 
          @toggle-read-mode="() => this.toggleReadMode()"
          /> -->
      <MenuBar
        v-if="editor && editable"
        :entity-name="entityName"
        :current-mode="currentMode" />
      <TextEditorFixedMenu :buttons="fixedMenu" />
    </div>
  </div>
  <TextEditorBubbleMenu
    v-if="editor && editable"
    :options="bubbleMenuOptions"
    :buttons="bubbleMenu" />
  <BubbleMenu
    v-if="isCommentModeOn"
    :editor="editor"
    :should-show="
      ({ editor }) =>
        isCommentModeOn &&
        !editor.state.selection.empty &&
        !activeCommentsInstance.uuid
    ">
    <div class="p-4 rounded-md border bg-white border-gray-100 shadow-lg">
      <textarea
        cols="50"
        rows="4"
        placeholder="Type your comment"
        style="resize: none"
        v-model="commentText"
        class="placeholder-gray-500 form-input block w-full mb-2"
        @keypress.enter.stop.prevent="() => setComment()" />
      <section class="flex justify-end gap-2">
        <Button @click="() => discardComment()">Discard</Button>
        <Button appearance="primary" @click="() => setComment()">Done</Button>
      </section>
    </div>
  </BubbleMenu>
  <div class="flex w-screen items-start justify-center space-x-4 mt-3">
    <editor-content
      id="editorElem"
      class="bg-white shadow-sm rounded-md border"
      :editor="editor" />
    <OuterCommentVue
      v-if="isCommentModeOn"
      :active-comments-instance="activeCommentsInstance"
      :all-comments="allComments"
      :focus-content="focusContent"
      :is-comment-mode-on="isCommentModeOn"
      @set-comment="setComment" />
  </div>
</template>

<script>
import { normalizeClass, computed } from "vue";
import { Editor, EditorContent, BubbleMenu } from "@tiptap/vue-3";
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
import { Button, Input } from "frappe-ui";
import { v4 as uuidv4 } from "uuid";
import { Comment } from "./comment";
import { LineHeight } from "./lineHeight";
import OuterCommentVue from "./OuterComment.vue";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import * as Y from "yjs";
import { WebrtcProvider } from "y-webrtc";

export default {
  name: "TextEditor",
  inheritAttrs: false,
  components: {
    EditorContent,
    BubbleMenu,
    TextEditorFixedMenu,
    TextEditorBubbleMenu,
    OuterCommentVue,
    MenuBar,
  },
  provide() {
    return {
      editor: computed(() => this.editor),
    };
  },
  expose: ["editor"],
  inheritAttrs: false,
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
    /* isWritable: {
      type: Boolean,
      default: true,
    }, */
    editable: {
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
      provider: null,
      tempEditable: false,
      isTextSelected: false,
      currentMode: "",
      commentText: "",
      isCommentModeOn: false,
      activeCommentsInstance: {
        uuid: "",
        comments: [],
      },
      allComments: [],
    };
  },
  methods: {
    getRandomColor() {
      const list = [
        "#958DF1",
        "#F98181",
        "#FBBC88",
        "#FAF594",
        "#70CFF8",
        "#94FADB",
        "#B9F18D",
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
    toggleCommentMode() {
      this.tempEditable = true;
      this.isCommentModeOn = true;
      this.currentMode = "Suggesting";
    },
    toggleEditMode() {
      this.tempEditable = true;
      this.isCommentModeOn = false;
      this.currentMode = "Editing";
    },
    toggleReadMode() {
      this.tempEditable = false;
      this.isCommentModeOn = false;
      this.currentMode = "Reading";
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
        setTimeout(() => (this.showCommentMenu = newVal), 50);
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
    /*     editable(){
          return this.isWritable && this.tempEditable
        }, */

    currentUserName() {
      return this.$store.state.user.fullName;
    },
    editorProps() {
      return {
        attributes: {
          class: normalizeClass([
            "prose prose-p:my-1 prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100",
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
    /*         allComments: {
      handler(newVal) {
        if (newVal) { // check if userid is available
          console.log(newVal)
        }
      },
      immediate: true // make this watch function is called when component created
    }, */
    /*     modelValue(value) {
      const isSame =
        JSON.stringify(this.editor.getJSON()) === JSON.stringify(value);
      if (isSame) {
        return;
      }
      this.editor.commands.setContent(value, false);
    }, */
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
    this.emitter.on("toggleCommentMode", () => {
      this.isCommentModeOn = true;
    });
    const doc = new Y.Doc();
    Y.applyUpdate(doc, this.modelValue);
    // https://github.com/yjs/y-webrtc/blob/master/bin/server.js
    const webrtcProvider = new WebrtcProvider(
      JSON.stringify(this.entityName),
      doc,
      { signaling: ["wss://network.arjun.lol"] }
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
            name: this.currentUserName,
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

        // This is incompatible with the `CollaborationCursor` extension
        // Refer to https://github.com/ueberdosis/tiptap/issues/4065
        /* Placeholder.configure({
          showOnlyWhenEditable: true,
          placeholder: () => {
            return this.placeholder;
          },
        }), */

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
  min-width: 816px;
  max-width: 816px;
  min-height: 1056px;
  padding: 2cm;
}

/* Firefox */
.ProseMirror-focused:focus-visible {
  outline: none;
}

span[data-comment] {
  background: rgba(2, 137, 255, 0.25);
  border-bottom: 2px rgb(2, 137, 255) solid;
  user-select: all;
  padding: 0 2px 0 2px;
  border-radius: 2px;
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
  border-radius: 3px 3px 3px 0;
  color: #0d0d0d;
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
  left: -1px;
  line-height: normal;
  padding: 0.1rem 0.3rem;
  position: absolute;
  top: -1.4em;
  user-select: none;
  white-space: nowrap;
}
</style>
