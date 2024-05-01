import { Mark, mergeAttributes, Range } from "@tiptap/core"
import { Mark as PMMark } from "@tiptap/pm/model"

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    annotation: {
      /**
       * Set annotation (add)
       */
      setAnnotation: (annotationID: string) => ReturnType
      /**
       * Unset a annotation (remove)
       */
      unsetAnnotation: (annotationID: string) => ReturnType
    }
  }
}

export interface MarkWithRange {
  mark: PMMark
  range: Range
}

export interface AnnotationOptions {
  HTMLAttributes: Record<string, any>
  onAnnotationActivated: (annotationID: string) => void
}

export interface AnnotationStorage {
  activeAnnotationId: string | null
}

export const AnnotationExtension = Mark.create<
  AnnotationOptions,
  AnnotationStorage
>({
  name: "annotation",
  excludes: "",
  // https://github.com/ueberdosis/tiptap/pull/2925
  // https://github.com/ueberdosis/tiptap/pull/1200
  // exitable: true, Validation needed
  inclusive: false,

  addOptions() {
    return {
      HTMLAttributes: {},
      onAnnotationActivated: () => {},
    }
  },

  addAttributes() {
    return {
      annotationID: {
        default: null,
        parseHTML: (el) =>
          (el as HTMLSpanElement).getAttribute("data-annotation-id"),
        renderHTML: (attrs) => ({ "data-annotation-id": attrs.annotationID }),
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: "span[data-annotation-id]",
        getAttrs: (el) =>
          !!(el as HTMLSpanElement)
            .getAttribute("data-annotation-id")
            ?.trim() && null,
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "span",
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes),
      0,
    ]
  },

  onSelectionUpdate() {
    const { $from } = this.editor.state.selection

    const marks = $from.marks()

    if (!marks.length) {
      this.storage.activeAnnotationId = null
      this.options.onAnnotationActivated(this.storage.activeAnnotationId)
      return
    }

    const annotationMark = this.editor.schema.marks.annotation

    const activeAnnotationMark = marks.find(
      (mark) => mark.type === annotationMark
    )

    this.storage.activeAnnotationId =
      activeAnnotationMark?.attrs.annotationID || null

    this.options.onAnnotationActivated(this.storage.activeAnnotationId)
  },

  addStorage() {
    return {
      activeAnnotationId: null,
    }
  },

  addCommands() {
    return {
      setAnnotation:
        (annotationID) =>
        ({ commands }) => {
          if (!annotationID) return false

          commands.setMark("annotation", { annotationID })
        },
      unsetAnnotation:
        (annotationID) =>
        ({ tr, dispatch }) => {
          if (!annotationID) return false

          const annotationMarksWithRange: MarkWithRange[] = []

          tr.doc.descendants((node, pos) => {
            const annotationMark = node.marks.find(
              (mark) =>
                mark.type.name === "annotation" &&
                mark.attrs.annotationID === annotationID
            )

            if (!annotationMark) return

            annotationMarksWithRange.push({
              mark: annotationMark,
              range: {
                from: pos,
                to: pos + node.nodeSize,
              },
            })
          })

          annotationMarksWithRange.forEach(({ mark, range }) => {
            tr.removeMark(range.from, range.to, mark)
          })

          return dispatch?.(tr)
        },
    }
  },
})
