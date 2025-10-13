import CommentExtension from "@sereneinserenade/tiptap-comment-extension"

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
