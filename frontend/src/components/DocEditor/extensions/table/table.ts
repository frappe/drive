import TiptapTable from "@tiptap/extension-table"
import TableRow from "./row"
import TableHeader from "./header"
import { TableCell } from "./cell"

import type { TableRowOptions } from "@tiptap/extension-table-row"
import type { TableHeaderOptions } from "./header"
import type { TableCellOptions } from "./cell"
import { GeneralOptions } from "@/type"

export interface TableOptions extends GeneralOptions<TableOptions> {
  HTMLAttributes: Record<string, any>
  resizable: boolean
  handleWidth: number
  cellMinWidth: number
  lastColumnResizable: boolean
  allowTableNodeSelection: boolean
  /** options for table rows */
  tableRow: Partial<TableRowOptions>
  /** options for table headers */
  tableHeader: Partial<TableHeaderOptions>
  /** options for table cells */
  tableCell: Partial<TableCellOptions>
  /** options for table cell background */
}
export const Table = TiptapTable.extend<TableOptions>({
  addOptions() {
    return {
      ...this.parent?.(),
      HTMLAttributes: {},
      resizable: true,
      lastColumnResizable: true,
      allowTableNodeSelection: false,
    }
  },
  addExtensions() {
    return [
      TableRow.configure(this.options.tableRow),
      TableHeader.configure(this.options.tableHeader),
      TableCell.configure(this.options.tableCell),
    ]
  },
})

export default Table
