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
    label: __("Bold"),
    icon: Bold,
    action: (editor) => editor.chain().focus().toggleBold().run(),
    isActive: (editor) => editor.isActive("bold"),
  },
  Italic: {
    label: __("Italic"),
    icon: Italic,
    action: (editor) => editor.chain().focus().toggleItalic().run(),
    isActive: (editor) => editor.isActive("italic"),
  },
  Underline: {
    label: __("Underline"),
    icon: Underline,
    action: (editor) => editor.chain().focus().toggleUnderline().run(),
    isActive: (editor) => editor.isActive("underline"),
  },
  Strikethrough: {
    label: __("Strikethrough"),
    icon: Strikethrough,
    action: (editor) => editor.chain().focus().toggleStrike().run(),
    isActive: (editor) => editor.isActive("strike"),
  },
  Code: {
    label: __("Code"),
    icon: Code,
    action: (editor) => editor.chain().focus().toggleCode().run(),
    isActive: (editor) => editor.isActive("code"),
  },
  Link: {
    label: __("New Link"),
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
    label: __("New Annotation"),
    icon: NewCommentIcon,
    isActive: (editor) => editor.isActive("comment"),
    component: defineAsyncComponent(() =>
      import("./components/NewAnnotation.vue")
    ),
  },
  Comment: {
    label: __("New Comment"),
    icon: NewLink,
    isActive: (editor) => editor.isActive("comment"),
    component: defineAsyncComponent(() =>
      import("./components/NewComment.vue")
    ),
  },
  MergeCells: {
    label: __("Merge Cells"),
    icon: TableCellsMerge,
    isActive: () => false,
    action: (editor) => editor.chain().focus().mergeCells().run(),
  },
  SplitCells: {
    label: __("Split Cells"),
    icon: TableCellsSplit,
    isActive: () => false,
    action: (editor) => editor.chain().focus().splitCell().run(),
  },
  ToggleHeaderCell: {
    label: __("Toggle Header"),
    icon: ToggleHeaderCell,
    isActive: () => false,
    action: (editor) => editor.chain().focus().toggleHeaderCell().run(),
  },
}
