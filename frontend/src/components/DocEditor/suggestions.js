import { VueRenderer } from "@tiptap/vue-3";
import { defineAsyncComponent, shallowReactive } from "vue";
import {
  Type,
  Heading1,
  Heading2,
  Heading3,
  Bold,
  Italic,
  UnderlineIcon,
  List,
  Table,
  ListOrdered,
  AlignCenter,
  AlignRight,
  AlignLeft,
  ImagePlus,
  Film,
} from "lucide-vue-next";
import tippy from "tippy.js";

import CommandsList from "./CommandsList.vue";

export default {
  items: ({ query }) => {
    return [
      {
        title: "Title",
        icon: Type,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 1 })
            .run();
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Heading 1",
        icon: Heading1,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 2 })
            .run();
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Heading 2",
        icon: Heading2,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 3 })
            .run();
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        /* Write custom subtitle node */
        title: "Subtitle",
        icon: Heading2,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 3 })
            .run();
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Heading 3",
        icon: Heading3,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 4 })
            .run();
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Bold",
        icon: Bold,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleBold().run();
        },
        disabled: (editor) => editor.isActive("bold"),
      },
      {
        title: "Italic",
        icon: Italic,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleItalic().run();
        },
        disabled: (editor) => editor.isActive("italic"),
      },
      {
        title: "Underline",
        icon: UnderlineIcon,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleUnderline().run();
        },
        disabled: (editor) => editor.isActive("underline"),
      },
      {
        title: "Bullet List",
        icon: List,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleBulletList().run();
        },
        disabled: (editor) => editor.isActive("bulletList"),
      },
      {
        title: "Ordered List",
        icon: ListOrdered,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleOrderedList().run();
        },
        disabled: (editor) => editor.isActive("bulletList"),
      },
      {
        title: "Align Center",
        icon: AlignCenter,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setTextAlign("center")
            .run();
        },
        disabled: (editor) => editor.isActive({ textAlign: "center" }),
      },
      {
        title: "Align Left",
        icon: AlignLeft,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).setTextAlign("left").run();
        },
        disabled: (editor) => editor.isActive({ textAlign: "left" }),
      },
      {
        title: "Align Right",
        icon: AlignRight,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).setTextAlign("right").run();
        },
        disabled: (editor) => editor.isActive({ textAlign: "right`" }),
      },
      {
        title: "Table",
        icon: Table,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
            .run();
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Add Column",
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).addColumnAfter().run();
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      {
        title: "Add Row",
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).addRowAfter().run();
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      {
        title: "Delete Column",
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).deleteColumn().run();
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      {
        title: "Delete Row",
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).deleteRow().run();
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      {
        title: "Delete Table",
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).deleteTable().run();
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      /*       shallowReactive({
        title: "Image",
        icon: ImagePlus,
        component: defineAsyncComponent(() => import("./InsertImage.vue")),
        isOpen: false,
      }),
      shallowReactive({
        title: "Video",
        icon: Film,
        component: defineAsyncComponent(() => import("./InsertVideo.vue")),
        isOpen: false,
      }), */
    ].filter((item) => item.title.toLowerCase().includes(query.toLowerCase()));
  },

  render: () => {
    let component;
    let popup;

    return {
      onStart: (props) => {
        component = new VueRenderer(CommandsList, {
          props,
          popup,
          editor: props.editor,
        });

        if (!props.clientRect) {
          return;
        }

        popup = tippy("body", {
          getReferenceClientRect: props.clientRect,
          appendTo: () => document.body,
          content: component.element,
          showOnCreate: true,
          interactive: true,
          trigger: "manual",
          placement: "bottom-start",
        });
      },

      onUpdate(props) {
        component.updateProps(props);
        component.updateProps(popup);
        console.log(props);
        console.log(popup);
        if (!props.clientRect) {
          return;
        }

        popup[0].setProps({
          getReferenceClientRect: props.clientRect,
        });
      },

      onKeyDown(props) {
        if (props.event.key === "Escape") {
          popup[0].hide();

          return true;
        }

        return component.ref?.onKeyDown(props);
      },

      onExit() {
        popup[0].destroy();
        component.destroy();
      },
    };
  },
};
