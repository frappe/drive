<template>
  <slot v-bind="{ onClick: openDialog }" />
  <Dialog
    v-model="showNewCommentDialog"
    :options="{ title: 'New Comment', size: 'sm' }"
    @after-leave="reset"
  >
    <template #body-content>
      <!-- <span class="text-sm italic font-medium leading-relaxed text-ink-gray-7">{{ `"${commentRootContent}"` }}</span> -->
      <!-- <span class="text-sm prose prose-xs overflow-auto" v-html="commentRootContent"></span> -->
      <!-- <span class="mt-4 mb-0.5 block text-sm leading-4 text-ink-gray-7">Comment</span> -->
      <textarea
        ref="input"
        v-model="commentText"
        class="resize-none w-full form-input mt-1 min-h-6 max-h-[50vh] text-sm"
        type="text"
        placeholder="Comment"
        @keydown.enter="(e) => setComment(e.target.value)"
      />
      <Button
        variant="solid"
        class="w-full mt-6"
        @click="setComment(commentText)"
      >
        Save
      </Button>
    </template>
    <!-- //https://github.com/ueberdosis/tiptap/issues/369 -->
  </Dialog>
</template>
<script>
import { Dialog, Button, Input } from "frappe-ui"
import { ref } from "vue"
import { useFocus } from "@vueuse/core"
import { v4 as uuidv4 } from "uuid"
import { DOMSerializer } from "prosemirror-model"

export default {
  name: "NewComment",
  components: { Button, Input, Dialog },
  props: ["editor"],
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
    commentRootContent() {
      const { view, state } = this.editor
      const { from, to } = view.state.selection
      return this.getHTMLContentBetween(this.editor, from, to)
      return state.doc.textBetween(from, to, "")
    },
  },
  watch: {
    commentText: function () {
      this.$refs.input.style.height = "2rem"
      this.$nextTick(() => {
        this.$refs.input.style.height = this.$refs.input.scrollHeight + "px"
      })
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
      const localVal = val || this.commentText
      const commentWithUuid = JSON.stringify({
        uuid: uuidv4(),
        comments: [
          {
            userName: this.currentUserName,
            userImage: this.currentUserImage,
            time: Date.now(),
            content: localVal,
          },
        ],
      })
      this.editor.chain().setComment(commentWithUuid).run()
      this.commentText = ""
      this.showNewCommentDialog = false
      this.$emit("success")
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
