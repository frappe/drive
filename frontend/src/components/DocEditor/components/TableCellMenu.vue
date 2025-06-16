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
  isTableCellSelected,
  isTableSelected,
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
export interface Emits {
  (event: "onDeleteTable"): void
  (event: "onMergeCell"): void
  (event: "onSplitCell"): void
  (event: "onHeaderCell"): void
}
const emits = defineEmits<Emits>()
const props = withDefaults(defineProps<Props>(), {})

const shouldShow = ({ view, state, from }: ShouldShowProps) => {
  if (!state) {
    return false
  }
  return isTableCellSelected({
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
</script>

<template>
  <BubbleMenu
    :editor="editor"
    pluginKey="tableCellMenu"
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
      class="flex flex-row h-full leading-none gap-0.5 p-0.5 bg-surface-white rounded shadow-sm border border-border"
    >
      <Button
        variant="ghost"
        v-if="Selection?.cellCount! > 1"
        @click="() => emits('onMergeCell')"
        ><template #icon><TableCellsMerge class="w-4 stroke-[1.5]" /></template
      ></Button>
      <Button
        variant="ghost"
        v-if="Selection?.mergedCellCount! > 0"
        @click="() => emits('onSplitCell')"
        ><template #icon>
          <TableCellsSplit class="w-4 stroke-[1.5]" /> </template
      ></Button>
      <Button
        variant="ghost"
        v-if="Selection?.mergedCellCount! > 0"
        @click="() => emits('onSplitCell')"
        ><template #icon>
          <TableCellsSplit class="w-4 stroke-[1.5]" /> </template
      ></Button>
      <Button
        variant="ghost"
        @click="() => emits('onHeaderCell')"
        ><template #icon>
          <ToggleHeaderCell class="w-4 stroke-[1.5]" /> </template
      ></Button>
      <Button
        v-if="isTableSelected(props.editor.state.selection)"
        icon="trash-2"
        @click="() => emits('onDeleteTable')"
      />
    </div>
  </BubbleMenu>
</template>
