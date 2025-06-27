<template>
  <TextEditor
    :editable="editable"
    :content="content"
    :mentions="allUsers.data"
    class="editor flex"
    :class="editable && 'border rounded'"
    :editor-class="['text-p-sm min-w-2 flex-grow', editable && 'p-2']"
    :placeholder
    @change="(val) => (editorContent = val)"
    :bubble-menu="[
      'Bold',
      'Italic',
      'Strikethrough',
      'Separator',
      'Code',
      'Blockquote',
      'Separator',
      ['Bullet List', 'Numbered List'],
    ]"
  >
    <template #bottom="{ editor }">
      <div
        v-if="editable"
        class="self-end me-1 flex-shrink-0 flex gap-1 mb-2"
      >
        <Button
          v-if="!isEmpty"
          :disabled
          variant="ghost"
          size="xs"
          class=""
          @click="$emit('submit', editor)"
        >
          <template #icon>
            <LucideMessageCircleReply class="size-4" />
          </template>
        </Button>
        <Button
          v-if="!isEmpty"
          :disabled
          variant="ghost"
          size="xs"
          class="font-medium"
          @click="$emit('cancel', editor)"
        >
          <template #icon>
            <LucideX class="w-4" />
          </template>
        </Button>
      </div>
    </template>
  </TextEditor>
</template>
<script setup>
import { TextEditor, Button } from "frappe-ui"
import { allUsers } from "@/resources/permissions"

const editorContent = defineModel({ type: String })

defineProps({
  placeholder: String,
  isEmpty: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  editable: { type: Boolean, default: true },
  content: { type: String, required: true },
})
defineEmits(["submit", "cancel"])
</script>
<style>
.editor > div:first-child {
  flex-grow: 1;
}
</style>
