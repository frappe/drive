<template>
  <div v-if="editable" class="relative w-full" :class="$attrs.class">
    <TextEditorBubbleMenu :editor="editor" :buttons="bubbleMenu" />
  </div>
  <slot name="editor" :editor="editor">
    <editor-content :editor="editor" />
  </slot>
</template>

<script>
import { normalizeClass, computed } from "vue";
import { Editor, EditorContent } from "@tiptap/vue-3";
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
import { Color } from "@tiptap/extension-color";
import configureMention from "./mention";
import TextEditorBubbleMenu from "./TextEditorBubbleMenu.vue";
import { detectMarkdown, markdownToHTML } from "../../utils/markdown";
import { DOMParser } from "prosemirror-model";
import SlashCommand from "./slashCommands.js";
import suggestion from "./suggestions.js";

export default {
  name: "TextEditor",
  components: {
    EditorContent,
    TextEditorBubbleMenu,
  },
  provide() {
    return {
      editor: computed(() => this.editor),
    };
  },
  inheritAttrs: false,
  props: {
    modelValue: {
      type: Object,
      default: null,
    },
    placeholder: {
      type: String,
      default: "",
    },
    editable: {
      type: Boolean,
      default: true,
    },
    bubbleMenu: {
      type: [Boolean, Array],
      default: false,
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
    };
  },
  computed: {
    editorProps() {
      return {
        attributes: {
          class: normalizeClass([
            "prose prose-p:my-1 prose-table:table-fixed prose-td:p-2 prose-th:p-2 prose-td:border prose-th:border prose-td:border-gray-300 prose-th:border-gray-300 prose-td:relative prose-th:relative prose-th:bg-gray-100",
            this.editorClass,
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
    modelValue(value) {
      const isSame =
        JSON.stringify(this.editor.getJSON()) === JSON.stringify(value);
      if (isSame) {
        return;
      }

      this.editor.commands.setContent(value, false);
    },

    editable(value) {
      this.editor.setEditable(value);
    },
    editorProps: {
      deep: true,
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
    this.editor = new Editor({
      content: this.modelValue,
      editorProps: this.editorProps,
      editable: this.editable,
      extensions: [
        StarterKit.configure({
          ...this.starterkitOptions,
        }),
        Table.configure({
          resizable: true,
        }),
        Underline,
        TableRow,
        TableHeader,
        TableCell,
        Typography,
        TextAlign.configure({
          types: ["heading", "paragraph"],
        }),
        TextStyle,
        Color,
        Highlight.configure({ multicolor: true }),
        Image,
        Video,
        Link.configure({
          openOnClick: false,
        }),
        Placeholder.configure({
          showOnlyWhenEditable: false,
          placeholder: () => {
            return this.placeholder;
          },
        }),
        SlashCommand.configure({ suggestion }),
        configureMention(this.mentions),
        ...(this.extensions || []),
      ],
      onUpdate: () => {
        this.$emit("update:modelValue", this.editor.getJSON());
      },
    });
  },
  beforeUnmount() {
    this.editor.destroy();
    this.editor = null;
  },
  expose: ["editor"],
};
</script>
