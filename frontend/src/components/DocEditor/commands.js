import { defineAsyncComponent } from "vue"
import { Code } from "lucide-vue-next"
import Bold from "./icons/Bold.vue"
import Italic from "./icons/Italic.vue"
import Strikethrough from "./icons/StrikeThrough.vue"
import Underline from "./icons/Underline.vue"
import NewAnnotation from "./icons/NewAnnotation.vue"
import NewLink from "./icons/NewLink.vue"
import { TableCellsSplit, TableCellsMerge } from "lucide-vue-next"
import ToggleHeaderCell from "./icons/ToggleHeaderCell.vue"

export default {
  Bold: {
    label: "Bold",
    icon: Bold,
    action: (editor) => editor.chain().focus().toggleBold().run(),
    isActive: (editor) => editor.isActive("bold"),
  },
  Italic: {
    label: "Italic",
    icon: Italic,
    action: (editor) => editor.chain().focus().toggleItalic().run(),
    isActive: (editor) => editor.isActive("italic"),
  },
  Underline: {
    label: "Underline",
    icon: Underline,
    action: (editor) => editor.chain().focus().toggleUnderline().run(),
    isActive: (editor) => editor.isActive("underline"),
  },
  Strikethrough: {
    label: "Strikethrough",
    icon: Strikethrough,
    action: (editor) => editor.chain().focus().toggleStrike().run(),
    isActive: (editor) => editor.isActive("strike"),
  },
  Code: {
    label: "Code",
    icon: Code,
    action: (editor) => editor.chain().focus().toggleCode().run(),
    isActive: (editor) => editor.isActive("code"),
  },
  Link: {
    label: "New Link",
    icon: NewLink,
    isActive: (editor) => editor.isActive("link"),
    component: defineAsyncComponent(() => import("./InsertLink.vue")),
  },
  Separator: {
    type: "separator",
  },
  Comment: {
    label: "New Comment",
    icon: NewAnnotation,
    isActive: (editor) => editor.isActive("comment"),
    component: defineAsyncComponent(() => import("./NewComment.vue")),
  },
  MergeCells: {
    label: "Merge Cells",
    icon: TableCellsMerge,
    isActive: () => false,
    action: (editor) => editor.chain().focus().mergeCells().run(),
  },
  SplitCells: {
    label: "Split Cells",
    icon: TableCellsSplit,
    isActive: () => false,
    action: (editor) => editor.chain().focus().splitCell().run(),
  },
  ToggleHeaderCell: {
    label: "Toggle Header",
    icon: ToggleHeaderCell,
    isActive: () => false,
    action: (editor) => editor.chain().focus().toggleHeaderCell().run(),
  },
}
