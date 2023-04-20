<template>
  <div v-if="editor" class="relative w-full" :class="$attrs.class">
    <TextEditorBubbleMenu :buttons="bubbleMenu" />
    <TextEditorFixedMenu
      class="w-full overflow-x-auto rounded-lg border border-gray-200"
      :buttons="fixedMenu" />
    <TextEditorFloatingMenu :buttons="floatingMenu" />
  </div>
  <slot name="top" />
  <slot name="editor" :editor="editor">
    <editor-content :editor="editor" />
  </slot>
  <slot name="bottom" />
</template>

<script>
import { normalizeClass, computed } from "vue";
import { Editor, EditorContent } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
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
import TextEditorFixedMenu from "./TextEditorFixedMenu.vue";
import TextEditorBubbleMenu from "./TextEditorBubbleMenu.vue";
import TextEditorFloatingMenu from "./TextEditorFloatingMenu.vue";
import { detectMarkdown, markdownToHTML } from "../../utils/markdown";
import { DOMParser } from "prosemirror-model";
/*  import { ColumnExtension } from "@gocapsule/column-extension"; */
import { ResizableMedia } from "./extensions/resizableMedia";

export default {
  name: "TextEditor",
  components: {
    EditorContent,
    TextEditorFixedMenu,
    TextEditorBubbleMenu,
    TextEditorFloatingMenu,
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
    editorClass: {
      type: [String, Array, Object],
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
    fixedMenu: {
      type: [Boolean, Array],
      default: false,
    },
    floatingMenu: {
      type: [Boolean, Array],
      default: false,
    },
    extensions: {
      type: Array,
      default: () => [],
    },
    starterkitOptions: {
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
        ResizableMedia,
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
  methods: {
    addImage() {
      this.editor.value?.commands.setMedia({
        src: "https://source.unsplash.com/8xznAGy4HcY/800x400",
        "media-type": "img",
        alt: "Something else",
        title: "Something",
        width: "800",
        height: "400",
      });
    },
  },
  expose: ["editor"],
};
</script>
<style>
.ProseMirror {
  outline: none;
  caret-color: theme("colors.blue.600");
  word-break: break-word;
  width: 21cm;
  min-height: 29.7cm;
  padding: 2cm;
  margin: 1cm auto;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.15);
}

/* Firefox */
.ProseMirror-focused:focus-visible {
  outline: none;
}

/* Placeholder */
.ProseMirror:not(.ProseMirror-focused) p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  float: left;
  color: theme("colors.gray.500");
  pointer-events: none;
  height: 0;
}

.ProseMirror-selectednode video,
img.ProseMirror-selectednode {
  border: 2px solid theme("colors.blue.300");
}

/* Mentions */
.mention {
  font-weight: 600;
  box-decoration-break: clone;
}

/* Table styles */
.prose table p {
  margin: 0;
}

/* Prosemirror specific table styles */
.ProseMirror table .selectedCell:after {
  z-index: 2;
  position: absolute;
  content: "";
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  pointer-events: none;
  background: theme("colors.blue.200");
  opacity: 0.3;
}

.ProseMirror table .column-resize-handle {
  position: absolute;
  right: -1px;
  top: 0;
  bottom: -2px;
  width: 4px;
  background-color: theme("colors.blue.200");
  pointer-events: none;
}

.resize-cursor {
  cursor: ew-resize;
  cursor: col-resize;
}

.ProseMirror mark {
  border-radius: 3px;
  padding: 0 2px;
}
.ProseMirror .column-block {
  width: 100%;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 24px;
  padding: 8px 0;
}

.ProseMirror .column {
  overflow: auto;
  border: 1px gray dashed;
  border-radius: 8px;
  padding: 8px;
  margin: -8px;
}

#editorElem {
  @page size: A4,;
}
</style>
