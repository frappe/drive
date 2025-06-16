<script setup lang="ts">
import { computed } from "vue"
import { Editor } from "@tiptap/vue-3"
import { BubbleMenu } from "@tiptap/vue-3"
import { Editor as CoreEditor } from "@tiptap/core"
import { EditorState } from "@tiptap/pm/state"
import { EditorView } from "@tiptap/pm/view"
import { NodeSelection } from "@tiptap/pm/state"
import { CellSelection } from "@tiptap/pm/tables"
import {
  analyzeCellSelection,
  isRowGripSelected,
} from "../extensions/table/utils"
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

  return isRowGripSelected({
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
  } else {
    return null
  }
})

function onAddRowBefore() {
  props.editor.chain().focus().addRowBefore().run()
}

function onAddRowAfter() {
  props.editor.chain().focus().addRowAfter().run()
}

function onDeleteRow() {
  props.editor.chain().focus().deleteRow().run()
}
</script>

<template>
  <BubbleMenu
    :editor="editor"
    pluginKey="tableRowMenu"
    :updateDelay="0"
    :should-show="shouldShow"
    :tippy-options="{
      appendTo: 'parent',
      placement: 'left',
      offset: [0, 5],
      popperOptions: {
        modifiers: [{ name: 'flip', enabled: false }],
      },
    }"
  >
    <div
      class="flex flex-col h-full leading-none bg-surface-white gap-0.5 p-0.5 rounded shadow-sm border border-border"
    >
      <Button
        title="Add Row Above"
        variant="ghost"
        icon="arrow-up"
        @click="onAddRowBefore"
      />

      <Button
        title="Add Row Below"
        variant="ghost"
        icon="arrow-down"
        @click="onAddRowAfter"
      />
      <Button
        title="Merge Cells"
        variant="ghost"
        v-if="Selection?.cellCount! > 1"
        @click="() => emits('onMergeCell')"
        ><template #icon><TableCellsMerge class="w-4 stroke-[1.5]" /></template
      ></Button>
      <Button
        title="Split Cells"
        variant="ghost"
        v-if="Selection?.mergedCellCount! > 0"
        @click="() => emits('onSplitCell')"
        ><template #icon>
          <TableCellsSplit class="w-4 stroke-[1.5]" /> </template
      ></Button>
      <Button
        title="Delete Row"
        variant="ghost"
        @click="() => emits('onHeaderCell')"
        ><template #icon>
          <ToggleHeaderCell class="w-4 stroke-[1.5]" /> </template
      ></Button>
      <Button
        variant="ghost"
        icon="trash-2"
        @click="onDeleteRow"
      />
    </div>
  </BubbleMenu>
</template>
