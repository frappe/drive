<template>
  <div>
    <slot v-bind="{ onClick: openDialog }" />
    <Dialog
      v-model="showNewCommentDialog"
      :options="{ title: 'New Annotation', size: 'sm' }"
      @after-leave="reset"
    >
      <template #body-content>
        <!-- <span class="text-sm italic font-medium leading-relaxed text-ink-gray-7">{{ `"${commentRootContent}"` }}</span> -->
        <!-- <span class="text-sm prose prose-xs overflow-auto" v-html="commentRootContent"></span> -->
        <!-- <span class="mt-4 mb-0.5 block text-sm leading-4 text-ink-gray-7">Comment</span> -->
        <TiptapInput
          v-model="commentText"
          class="border border-outline-gray-2"
          :show-inline-button="false"
          @keyup.ctrl.enter="setComment(commentText)"
        />
        <Button
          variant="solid"
          class="w-full mt-6"
          @click="setComment(commentText)"
        >
          Post
        </Button>
      </template>
      <!-- //https://github.com/ueberdosis/tiptap/issues/369 -->
    </Dialog>
  </div>
</template>
<script>
import { Dialog, Button } from "frappe-ui"
import { ref } from "vue"
import { useFocus } from "@vueuse/core"
import { v4 as uuidv4 } from "uuid"
import { DOMSerializer } from "prosemirror-model"
import * as Y from "yjs"
import TiptapInput from "@/components/TiptapInput.vue"

export default {
  name: "NewComment",
  components: { Button, Dialog, TiptapInput },
  inject: ["editor", "document"],
  setup() {
    const input = ref(null)
    const { focused } = useFocus(input, { initialValue: true })
    return {
      input,
      focused,
    }
  },
  data() {
    return {
      commentText: "",
      showNewCommentDialog: false,
      activeCommentsInstance: {
        uuid: "",
        comments: [],
      },
    }
  },
  computed: {
    currentUserName() {
      return this.$store.state.user.fullName
    },
    currentUserImage() {
      return this.$store.state.user.imageURL
    },
    currentUserEmail() {
      return this.$store.state.user.id
    },
    commentRootContent() {
      const { view, state } = this.editor
      const { from, to } = view.state.selection
      return this.getHTMLContentBetween(this.editor, from, to)
      return state.doc.textBetween(from, to, "")
    },
  },
  computed: {
    currentUserName() {
      return this.$store.state.user.fullName
    },
    currentUserImage() {
      return this.$store.state.user.imageURL
    },
    commentRootContent() {
      const { view, state } = this.editor
      const { from, to } = view.state.selection
      return this.getHTMLContentBetween(this.editor, from, to)
      return state.doc.textBetween(from, to, "")
    },
  },
  methods: {
    openDialog() {
      this.emitter.emit("forceHideBubbleMenu", true)
      this.showNewCommentDialog = true
    },
    getHTMLContentBetween(editor, from, to) {
      const { state } = editor
      const nodesArray = []

      state.doc.nodesBetween(from, to, (node, pos, parent) => {
        if (parent === state.doc) {
          const serializer = DOMSerializer.fromSchema(editor.schema)
          const dom = serializer.serializeNode(node)
          const tempDiv = document.createElement("div")
          tempDiv.appendChild(dom)
          nodesArray.push(tempDiv.innerHTML)
        }
      })

      return nodesArray.join("")
    },
    setComment(val) {
      // Trim trailing whitespace
      let { from, to } = this.editor.view.state.selection
      const textContent = this.editor.view.state.doc.textBetween(from, to)
      const trimmedEnd = textContent.length - textContent.trim().length
      to = to - trimmedEnd
      this.editor.commands.setTextSelection({ from, to })
      const newID = uuidv4()
      const newCommentRepliesYarray = new Y.Array()
      const newCommentYmap = new Y.Map()
      newCommentYmap.set("id", newID)
      newCommentYmap.set("content", val)
      newCommentYmap.set("anchor", 1)
      newCommentYmap.set("resolved", 0)
      //newCommentYmap.set('synced', 1)
      newCommentYmap.set("owner", this.currentUserName)
      newCommentYmap.set("ownerEmail", this.$store.state.user.id)
      newCommentYmap.set("ownerImage", this.currentUserImage)
      newCommentYmap.set("replies", newCommentRepliesYarray)
      newCommentYmap.set("createdAt", Date.now())
      newCommentYmap.set("rangeStart", from)
      newCommentYmap.set("rangeEnd", to)

      const yarray = this.document.getArray("docAnnotations")
      yarray.push([newCommentYmap])
      this.editor.chain().setAnnotation(newID).run()

      /* let newComment = {
          id: uuidv4(),
          content: val,
          anchor: 1,
          resolved: 0,
          synced: 1,
          owner: this.currentUserName,
          ownerEmail: this.currentUserEmail,
          replies: [],
          createdAt: Date.now(),
          rangeStart: from,
          rangeEnd: to,
        } */

      this.commentText = ""
      this.showNewCommentDialog = false
      this.$emit("success")

      /*         // Get all marks in this selection
        let activeCommentsInSelection = []
        this.editor.state.doc.nodesBetween(from, to, (node) => {
          const mark = node.marks.find((mark) => mark.type.name === 'comment');
          if (mark) {
            activeCommentsInSelection.push(mark);
          }
        });
        let id1 = activeCommentsInSelection[0].attrs.commentId
        let id2 = activeCommentsInSelection[1].attrs.commentId
        id1 = activeCommentsInSelection[1].attrs.commentId
        console.log(activeCommentsInSelection[0].attrs.commentId) */
      /*         const isCommentActive = activeMarks.some(mark => mark.type.name === 'comment');

        if (isCommentActive) {
           // Find the first active 'comment' mark
           const firstCommentMark = activeMarks.find(mark => mark.type.name === 'comment');
           // Get the attributes of the 'comment' mark
           const firstCommentAttrs = firstCommentMark.attrs;
           console.log('The first active comment mark here is:', firstCommentMark)
           console.log('The first active comment markAttrs here is:', firstCommentAttrs)
          } else {
            console.log('Not Active.');
          } */
    },
    discardComment() {
      this.activeCommentsInstance = {}
      this.commentText = ""
    },
    reset() {
      this.emitter.emit("forceHideBubbleMenu", false)
      this.showNewCommentDialog = this.$options.data().showNewCommentDialog
    },
  },
}
</script>
