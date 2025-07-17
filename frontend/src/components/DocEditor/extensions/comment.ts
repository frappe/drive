import { Editor, Extension } from "@tiptap/core"
import { Plugin, PluginKey } from "@tiptap/pm/state"
import { EditorView } from "@tiptap/pm/view"
import { DOMSerializer } from "@tiptap/pm/model"
import tippy, { Instance } from "tippy.js"

class FloatingQuoteButtonView {
  public button: HTMLButtonElement
  private editorView: EditorView
  private tippyInstance: Instance | null = null
  private editor: Editor

  constructor(editorView: EditorView, editor: Editor) {
    this.editorView = editorView
    this.editor = editor
    this.button = document.createElement("button")
    this.button.textContent = "Comment"
    let classes = [
      "h-7 text-ink-white bg-surface-gray-7 hover:bg-surface-gray-6 active:bg-surface-gray-5",
      "text-ink-gray-8 bg-surface-gray-2 hover:bg-surface-gray-3 active:bg-surface-gray-4",
      "focus-visible:ring focus-visible:ring-outline-gray-3",
      "h-7 text-base px-2 rounded inline-flex items-center justify-center gap-2 transition-colors focus:outline-none",
    ]
      .map((c) => c.split(" "))
      .flat()
    this.button.classList.add(...classes)

    this.button.addEventListener("mousedown", (event) => {
      event.preventDefault()

      const { from, to } = this.editorView.state.selection
      const slice = this.editorView.state.doc.slice(from, to)

      const serializer = DOMSerializer.fromSchema(this.editorView.state.schema)
      const domFragment = serializer.serializeFragment(slice.content)
      const tempDiv = document.createElement("div")
      tempDiv.appendChild(domFragment)
      const selectedHTML = tempDiv.innerHTML

      const extensionOptions = this.editor.options.extensions.find(
        (e) => e.name === "floatingQuoteButton"
      )?.options
      if (extensionOptions && typeof extensionOptions.onClick === "function") {
        extensionOptions.onClick(selectedHTML)
      }

      this.tippyInstance?.hide()
    })

    this.update(editorView, null)
  }

  private handleScroll = () => {
    if (this.tippyInstance?.state.isVisible) {
      this.tippyInstance.hide()
    }
  }

  update(view: EditorView) {
    const { state } = view
    const { selection } = state

    if (view.editable) {
      this.tippyInstance?.hide()
      return
    }

    if (
      !selection.empty &&
      selection.from !== selection.to &&
      selection.node?.type.name !== "richQuote"
    ) {
      const rect = getRectForSelection(view)

      if (rect && (rect.width > 0 || rect.height > 0)) {
        if (!this.tippyInstance) {
          this.tippyInstance = tippy(this.editorView.dom, {
            content: this.button,
            trigger: "manual",
            interactive: true,
            placement: "top",
            arrow: false,
            appendTo: () => document.body,
            hideOnClick: true,
            duration: 150,
            onShow: () => {
              window.addEventListener("scroll", this.handleScroll, true)
            },
            onHide: () => {
              window.removeEventListener("scroll", this.handleScroll, true)
            },
          })
        }
        this.tippyInstance?.setProps({
          getReferenceClientRect: () => rect,
        })
        this.tippyInstance?.show()
      } else {
        this.tippyInstance?.hide()
      }
    } else {
      this.tippyInstance?.hide()
    }
  }

  destroy() {
    window.removeEventListener("scroll", this.handleScroll, true)
    this.tippyInstance?.destroy()
  }
}

export const FloatingQuoteButton = Extension.create({
  name: "floatingQuoteButton",

  addOptions() {
    return {
      onClick: (html: string) => {
        console.warn("FloatingQuoteButton: onClick not implemented.", html)
      },
    }
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey("floatingQuoteButton"),
        view: (editorView) =>
          new FloatingQuoteButtonView(editorView, this.editor),
      }),
    ]
  },
})

function getRectForSelection(view: EditorView): DOMRect | null {
  const { state } = view
  const { selection } = state
  if (selection.empty || selection.from === selection.to) return null

  const { from, to } = selection

  const pmRange = document.createRange()
  try {
    const startNode = view.domAtPos(from).node
    const startOffset = view.domAtPos(from).offset
    const endNode = view.domAtPos(to).node
    const endOffset = view.domAtPos(to).offset

    pmRange.setStart(startNode, startOffset)
    pmRange.setEnd(endNode, endOffset)
    const rect = pmRange.getBoundingClientRect()
    // Ensure the rect has non-zero dimensions, otherwise tippy might not show
    if (rect.width === 0 && rect.height === 0 && from !== to) {
      // Fallback for collapsed or problematic ranges that are not truly empty selections
      const startCoords = view.coordsAtPos(from)
      const endCoords = view.coordsAtPos(to)
      return new DOMRect(
        startCoords.left,
        startCoords.top,
        // Ensure width/height is not negative
        Math.max(0, endCoords.right - startCoords.left),
        Math.max(0, endCoords.bottom - startCoords.top)
      )
    }
    return rect
  } catch (e) {
    console.warn("Error creating DOM range for selection:", e)
    // Fallback to coordsAtPos if DOM range creation fails
    const startCoords = view.coordsAtPos(from)
    const endCoords = view.coordsAtPos(to)
    return new DOMRect(
      startCoords.left,
      startCoords.top,
      endCoords.right - startCoords.left,
      endCoords.bottom - startCoords.top
    )
  }
}

export default FloatingQuoteButton
