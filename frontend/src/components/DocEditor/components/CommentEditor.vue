<template>
  <div
    class="w-full"
    @keydown.ctrl.enter.capture.stop="
      !disabled && !isEmpty && $emit('submit', editor)
    "
    @keydown.meta.enter.capture.stop="
      !disabled && !isEmpty && $emit('submit', editor)
    "
    @keydown.esc.stop="$emit('cancel', editor)"
  >
    <TextEditor
      :autofocus="true"
      ref="textEditor"
      :editable="editable"
      :content="content"
      :mentions="allUsers.data"
      class="editor flex"
      :class="editable && 'border rounded'"
      :editor-class="[
        'text-p-sm min-w-2 flex-grow',
        editable && 'pl-2.5 py-1.5',
      ]"
      :placeholder
      @change="
        (val) => {
          $emit('change')
          editorContent = val
        }
      "
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
          class="self-end me-1 flex-shrink-0 flex gap-1 mb-1.5"
        >
          <Button
            v-if="!isEmpty"
            :disabled
            variant="ghost"
            class="!h-5 !w-5 !text-xs !rounded-sm"
            @click="$emit('submit', editor)"
          >
            <template #icon>
              <LucideMessageCircleReply class="size-3.5" />
            </template>
          </Button>
          <Button
            v-if="!isEmpty"
            variant="ghost"
            class="!h-5 !w-5 !text-xs !rounded-sm"
            @click="$emit('cancel', editor)"
          >
            <template #icon>
              <LucideX class="w-3.5" />
            </template>
          </Button>
        </div>
      </template>
    </TextEditor>
  </div>
</template>
<script setup>
import { TextEditor, Button } from "frappe-ui"
import { allUsers } from "@/resources/permissions"
import { computed, ref } from "vue"

const editorContent = defineModel({ type: String })

const textEditor = ref("textEditor")
const editor = computed(() => {
  return textEditor.value?.editor
})

defineProps({
  placeholder: String,
  isEmpty: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  editable: { type: Boolean, default: true },
  content: { type: String, default: "" },
})
defineEmits(["submit", "cancel", "change"])
</script>
<style>
.editor > div:first-child {
  flex-grow: 1;
}
</style>
