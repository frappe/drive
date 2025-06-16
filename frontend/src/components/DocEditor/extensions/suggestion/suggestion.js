import { VueRenderer } from "@tiptap/vue-3"
import {
  Type,
  Heading1,
  Heading2,
  Table,
  Minus,
  ArrowRight,
  ArrowDown,
} from "lucide-vue-next"
import tippy from "tippy.js"
import List from "../../icons/List.vue"
import OrderList from "../../icons/OrderList.vue"
import Check from "../../icons/Check.vue"
import Codeblock from "../../icons/Codeblock.vue"
import BlockQuote from "../../icons/BlockQuote.vue"
import Image from "../../icons/Image.vue"
import Video from "../../icons/Video.vue"
import PageBreak from "../../icons/PageBreak.vue"
import CommandsList from "../../components/suggestionList.vue"
import Mention from "../../icons/Mention.vue"
import emitter from "@/emitter"

export default {
  items: ({ query }) => {
    return [
      {
        title: "Style",
        type: "Section",
        //disabled: () => false,
      },
      {
        title: "Title",
        icon: Type,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 1 })
            .run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Subtitle",
        icon: Heading1,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 2 })
            .run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Heading",
        icon: Heading2,
        command: ({ editor, range }) => {
          editor
            .chain()
            .focus()
            .deleteRange(range)
            .setNode("heading", { level: 3 })
            .run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Ordered List",
        icon: OrderList,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleOrderedList().run()
        },
        disabled: (editor) => editor.isActive("bulletList"),
      },
      {
        title: "Bullet List",
        icon: List,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleBulletList().run()
        },
        disabled: (editor) => editor.isActive("bulletList"),
      },
      {
        title: "Task List",
        icon: Check,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleTaskList().run()
        },
        disabled: (editor) => editor.isActive("bulletList"),
      },
      {
        title: "Code Block",
        icon: Codeblock,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleCodeBlock().run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Focus Block",
        icon: BlockQuote,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).toggleBlockquote().run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Mention",
        icon: Mention,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).insertContent("@").run()
        },
        disabled: () => false,
      },
      {
        title: "Insert",
        type: "Section",
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
            .run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Add Column",
        icon: ArrowRight,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).addColumnAfter().run()
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      {
        title: "Add Row",
        icon: ArrowDown,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).addRowAfter().run()
        },
        disabled: (editor) => !editor.isActive("table"),
      },
      {
        title: "Image",
        icon: Image,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).run()
          emitter.emit("addImage")
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Video",
        icon: Video,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).run()
          emitter.emit("addVideo")
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Horizontal rule",
        icon: Minus,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).setHorizontalRule().run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
      {
        title: "Page Break",
        icon: PageBreak,
        command: ({ editor, range }) => {
          editor.chain().focus().deleteRange(range).setPageBreak().run()
        },
        disabled: (editor) => editor.isActive("table"),
      },
    ].filter((item) => item.title.toLowerCase().includes(query.toLowerCase()))
  },

  render: () => {
    let component
    let popup

    return {
      onStart: (props) => {
        component = new VueRenderer(CommandsList, {
          props,
          popup,
          editor: props.editor,
        })

        if (!props.clientRect) {
          return
        }

        popup = tippy("body", {
          getReferenceClientRect: props.clientRect,
          appendTo: () => document.body,
          content: component.element,
          showOnCreate: true,
          interactive: true,
          trigger: "manual",
          placement: "bottom-start",
        })
      },

      onUpdate(props) {
        component.updateProps(props)
        component.updateProps(popup)
        if (!props.clientRect) {
          return
        }

        popup[0].setProps({
          getReferenceClientRect: props.clientRect,
        })
      },

      onKeyDown(props) {
        if (props.event.key === "Escape") {
          popup[0].hide()

          return true
        }

        return component.ref?.onKeyDown(props)
      },

      onExit() {
        popup[0].destroy()
        component.destroy()
      },
    }
  },
}
