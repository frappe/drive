<template>
  <div
    class="flex items-center min-h-7 justify-start border border-outline-gray-modals rounded pl-2 pr-1 py-0.5 hover:border-outline-gray-modals focus-within:bg-surface-white focus-within:border-outline-gray-4 focus-within:shadow-sm focus-within:ring-2 focus-within:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full"
  >
    <editor-content
      class="w-full"
      :editor="editor"
    />
    <!-- Take this out later -->
    <Button
      v-if="showInlineButton"
      class="mt-auto ml-auto hover:bg-surface-gray-4 min-w-7 aspect-square cursor-pointer"
      :variant="'ghost'"
      icon="arrow-up-circle"
      :disabled="!modelValue.length"
      @click="$emit('success', modelValue)"
    />
  </div>
</template>
<script>
import { Button } from "frappe-ui"
import { normalizeClass } from "vue"
import { Document } from "@/components/DocEditor/extensions/document"
import { Paragraph } from "@/components/DocEditor/extensions/paragraph"
import { Text } from "@/components/DocEditor/extensions/text"
import { Editor, EditorContent } from "@tiptap/vue-3"
import { Placeholder } from "./DocEditor/extensions/placeholder"

export default {
  components: {
    EditorContent,
    Button,
  },
  props: {
    modelValue: {
      type: String,
      default: "",
    },
    showInlineButton: {
      type: Boolean,
      default: true,
      required: false,
    },
  },
  emits: ["update:modelValue", "success"],

  data() {
    return {
      editor: null,
    }
  },
  watch: {
    modelValue(value) {
      const isSame = this.editor.getHTML() === value
      if (isSame) {
        return
      }

      this.editor.commands.setContent(value, false)
    },
  },
  mounted() {
    this.editor = new Editor({
      autofocus: true,
      extensions: [
        Document,
        Paragraph,
        Text,
        Placeholder.configure({
          placeholder: "Ctrl + Enter to post",
        }),
      ],
      editorProps: {
        attributes: {
          class: normalizeClass([
            `text-sm !p-0 min-w-full placeholder-ink-gray-4 bg-surface-gray-2 !bg-transparent border-0 resize-none focus:outline-0 focus:border-0 active:outline-0 hover:bg-transparent`,
          ]),
        },
      },
      content: this.modelValue,
      onUpdate: () => {
        this.$emit("update:modelValue", this.editor.getHTML())
      },
    })
  },

  beforeUnmount() {
    this.editor.destroy()
  },
}
</script>
