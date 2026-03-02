import { Mark, mergeAttributes } from "@tiptap/core"

const CommentExtension = Mark.create({
  name: "comment",

  addOptions() {
    return {
      HTMLAttributes: {},
      onCommentActivated: () => {},
    }
  },

  addAttributes() {
    return {
      commentId: {
        default: null,
        parseHTML: (el) => el.getAttribute("data-comment-id"),
        renderHTML: (attrs) => ({ "data-comment-id": attrs.commentId }),
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: "span[data-comment-id]",
        getAttrs: (el) => !!el.getAttribute("data-comment-id")?.trim() && null,
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
      this.storage.activeCommentId = null
      this.options.onCommentActivated(this.storage.activeCommentId)
      return
    }

    const commentMark = this.editor.schema.marks.comment

    const activeCommentMark = marks.find((mark) => mark.type === commentMark)

    this.storage.activeCommentId = activeCommentMark?.attrs.commentId || null

    this.options.onCommentActivated(this.storage.activeCommentId)
  },

  addStorage() {
    return {
      activeCommentId: null,
    }
  },

  addCommands() {
    return {
      setComment:
        (commentId) =>
        ({ commands }) => {
          if (!commentId) return false

          commands.setMark("comment", { commentId })
        },
      unsetComment:
        (commentId) =>
        ({ tr, dispatch }) => {
          if (!commentId) return false

          const commentMarksWithRange = []

          tr.doc.descendants((node, pos) => {
            const commentMark = node.marks.find(
              (mark) =>
                mark.type.name === "comment" &&
                mark.attrs.commentId === commentId
            )

            if (!commentMark) return

            commentMarksWithRange.push({
              mark: commentMark,
              range: {
                from: pos,
                to: pos + node.nodeSize,
              },
            })
          })

          commentMarksWithRange.forEach(({ mark, range }) => {
            tr.removeMark(range.from, range.to, mark)
          })

          return dispatch?.(tr)
        },
    }
  },
})

export default CommentExtension.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      resolved: {
        default: false,
        parseHTML: (el) => el.hasAttribute("data-resolved"),
        renderHTML: (attrs) =>
          attrs.resolved ? { "data-resolved": "true" } : {},
      },
    }
  },
  addCommands() {
    return {
      ...this.parent?.(),

      resolveComment:
        (commentId, resolved = true) =>
        ({ state, tr, dispatch }) => {
          const { doc } = state
          const markType = state.schema.marks[this.name]

          doc.descendants((node, pos) => {
            if (!node.isText) return true
            node.marks.forEach((mark) => {
              if (
                mark.type === markType &&
                mark.attrs.commentId === commentId
              ) {
                const updatedMark = markType.create({
                  ...mark.attrs,
                  resolved,
                })

                tr.removeMark(pos, pos + node.nodeSize, markType)
                tr.addMark(pos, pos + node.nodeSize, updatedMark)
              }
            })
          })

          if (tr.docChanged && dispatch) {
            dispatch(tr)
            return true
          }

          return false
        },
    }
  },
})
