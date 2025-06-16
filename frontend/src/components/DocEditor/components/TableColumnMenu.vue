<script setup lang="ts">
import { computed } from "vue"
import type { Editor } from "@tiptap/vue-3"
import { BubbleMenu } from "@tiptap/vue-3"
import { Editor as CoreEditor } from "@tiptap/core"
import { EditorState } from "@tiptap/pm/state"
import { EditorView } from "@tiptap/pm/view"
import type { NodeSelection } from "@tiptap/pm/state"
import { CellSelection } from "@tiptap/pm/tables"
import {
  analyzeCellSelection,
  isColumnGripSelected,
} from "../extensions/table/utils"
import { Button } from "frappe-ui"
import { TableCellsMerge, TableCellsSplit } from "lucide-vue-next"
import ToggleHeaderCell from "../icons/ToggleHeaderCell.vue"

interface Props {
  editor: Editor
}
export interface ShouldShowProps {
  editor?: CoreEditor
  view: EditorView
  state?: EditorState
  oldState?: EditorState
  from?: number
  to?: number
}

const props = withDefaults(defineProps<Props>(), {})

export interface Emits {
  (event: "onMergeCell"): void
  (event: "onSplitCell"): void
  (event: "onHeaderCell"): void
}
const emits = defineEmits<Emits>()

const shouldShow = ({ view, state, from }: ShouldShowProps) => {
  if (!state) {
    return false
  }
  return isColumnGripSelected({
    editor: props.editor,
    view,
    state,
    from: from || 0,
  })
}

const Selection = computed(() => {
  const NodeSelection = props.editor.state.selection as NodeSelection
  const isCell = NodeSelection instanceof CellSelection
  if (isCell) {
    return analyzeCellSelection(props.editor)
  }
  {
    return null
  }
})

function onAddColumnBefore() {
  props.editor.chain().focus().addColumnBefore().run()
}

function onAddColumnAfter() {
  props.editor.chain().focus().addColumnAfter().run()
}

function onDeleteColumn() {
  props.editor.chain().focus().deleteColumn().run()
}
</script>

<template>
  <BubbleMenu
    :editor="editor"
    pluginKey="tableColumnMenu"
    :updateDelay="0"
    :should-show="shouldShow"
    :tippy-options="{
      appendTo: 'parent',
      offset: [0, 15],
      popperOptions: {
        modifiers: [{ name: 'flip', enabled: false }],
      },
    }"
  >
    <div
      class="min-w-32 flex flex-row h-full leading-none gap-0.5 p-0.5 bg-surface-white rounded shadow-sm border"
    >
      <Button
        title="Insert Row Left"
        variant="ghost"
        icon="arrow-left"
        @click="onAddColumnBefore"
      />
      <Button
        title="Insert Row Right"
        variant="ghost"
        icon="arrow-right"
        @click="onAddColumnAfter"
      />
      <Button
        variant="ghost"
        title="Merge Cells"
        v-if="Selection?.cellCount! > 1"
        @click="emits('onMergeCell')"
        ><template #icon><TableCellsMerge class="w-4 stroke-[1.5]" /></template
      ></Button>
      <Button
        variant="ghost"
        title="Split Cells"
        v-if="Selection?.mergedCellCount! > 0"
        @click="emits('onSplitCell')"
      >
        <template #icon> <TableCellsSplit class="w-4 stroke-[1.5]" /> </template
        >Split Cells
      </Button>
      <Button
        variant="ghost"
        @click="() => emits('onHeaderCell')"
        ><template #icon>
          <ToggleHeaderCell class="w-4 stroke-[1.5]" /> </template
      ></Button>
      <Button
        title="Delete Column"
        variant="ghost"
        icon="trash-2"
        @click="onDeleteColumn"
      />
    </div>
  </BubbleMenu>
</template>
