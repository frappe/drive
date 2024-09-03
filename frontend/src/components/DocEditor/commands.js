import { defineAsyncComponent } from "vue"
import { Code } from "lucide-vue-next"
import Bold from "./icons/Bold.vue"
import Italic from "./icons/Italic.vue"
import Strikethrough from "./icons/StrikeThrough.vue"
import Underline from "./icons/Underline.vue"
import { default as NewCommentIcon } from "../EspressoIcons/Comment.vue"
import { default as NewLink } from "../EspressoIcons/Link.vue"
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
    component: defineAsyncComponent(() =>
      import("./components/InsertLink.vue")
    ),
  },
  Separator: {
    type: "separator",
  },
  NewAnnotation: {
    label: "New Annotation",
    icon: NewCommentIcon,
    isActive: (editor) => editor.isActive("comment"),
    component: defineAsyncComponent(() =>
      import("./components/NewAnnotation.vue")
    ),
  },
  Comment: {
    label: "New Comment",
    icon: NewLink,
    isActive: (editor) => editor.isActive("comment"),
    component: defineAsyncComponent(() =>
      import("./components/NewComment.vue")
    ),
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
