<template>
  <slot v-bind="{ onClick: openDialog }" />
  <Dialog
    v-model="setLinkDialog.show"
    :options="{ title: setLinkDialog.title, size: 'sm' }"
    @after-leave="reset"
  >
    <template #body-content>
      <span
        class="text-sm italic font-medium leading-relaxed text-ink-gray-8"
        >{{ `"${linkRootContent}"` }}</span
      >
      <Input
        ref="input"
        v-model="setLinkDialog.url"
        type="text"
        class="mt-1"
        placeholder="Link"
        @keydown.enter="(e) => setLink(e.target.value)"
      />
      <Button
        variant="solid"
        class="w-full mt-6"
        @click="setLink(setLinkDialog.url)"
      >
        Save
      </Button>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, Button, Input } from "frappe-ui"
import { ref } from "vue"
import { useFocus } from "@vueuse/core"

export default {
  name: "InsertLink",
  components: { Button, Input, Dialog },
  props: ["editor"],
  setup() {
    const input = ref()
    const { focused } = useFocus(input, { initialValue: true })
    return {
      input,
      focused,
    }
  },
  data() {
    return {
      setLinkDialog: { title: "Set Link", url: "", show: false },
    }
  },
  computed: {
    linkRootContent() {
      const { view, state } = this.editor
      const { from, to } = view.state.selection
      return state.doc.textBetween(from, to, "")
    },
  },
  methods: {
    openDialog() {
      this.emitter.emit("forceHideBubbleMenu", true)
      let existingURL = this.editor.getAttributes("link").href
      if (existingURL) {
        this.setLinkDialog.url = existingURL
        this.setLinkDialog.title = "Edit Link"
      }
      this.setLinkDialog.show = true
    },
    setLink(url) {
      // empty
      if (url === "") {
        this.editor.chain().focus().extendMarkRange("link").unsetLink().run()
      } else {
        // update link
        this.editor
          .chain()
          .focus()
          .extendMarkRange("link")
          .setLink({ href: url })
          .run()
      }

      this.setLinkDialog.show = false
      this.setLinkDialog.url = ""
    },
    reset() {
      this.emitter.emit("forceHideBubbleMenu", false)
      this.setLinkDialog = this.$options.data().setLinkDialog
    },
  },
}
</script>
