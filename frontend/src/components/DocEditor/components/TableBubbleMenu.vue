<script setup lang="ts">
import type { Editor } from "@tiptap/vue-3"
import { CellSelection } from "@tiptap/pm/tables"

import TableCellMenu from "./TableCellMenu.vue"
import TableRowMenu from "./TableRowMenu.vue"
import TableColumnMenu from "./TableColumnMenu.vue"

interface Props {
  editor: Editor
}
const props = withDefaults(defineProps<Props>(), {})

function onDeleteTable() {
  props.editor.chain().focus().deleteTable().run()
}

function onMergeCell() {
  props.editor.chain().focus().mergeCells().run()
}

function onHeaderCell() {
  props.editor.chain().focus().toggleHeaderCell().run()
}

function onSplitCell() {
  const posQueue: Array<number> = []
  ;(props.editor.state.selection as CellSelection).forEachCell((cell, pos) => {
    if (cell.attrs.colspan > 1 || cell.attrs.rowspan > 1) {
      posQueue.push(pos)
    }
  })
  let chain = props.editor.chain()
  posQueue
    .sort((x, y) => y - x)
    .forEach((pos) => {
      chain = chain.setCellSelection({ anchorCell: pos }).splitCell()
    })
  chain.run()
}
</script>
<template>
  <TableCellMenu
    :editor="editor"
    @on-split-cell="onSplitCell"
    @on-header-cell="onHeaderCell"
    @on-merge-cell="onMergeCell"
    @on-delete-table="onDeleteTable"
  />
  <TableColumnMenu
    :editor="editor"
    @on-split-cell="onSplitCell"
    @on-header-cell="onHeaderCell"
    @on-merge-cell="onMergeCell"
  />
  <TableRowMenu
    :editor="editor"
    @on-split-cell="onSplitCell"
    @on-header-cell="onHeaderCell"
    @on-merge-cell="onMergeCell"
  />
</template>
