<template>
  <Dialog
    v-model="open"
    :options="{
      title: dialogTitle,
      size: 'xs',
      actions: [
        {
          label: __('Create'),
          variant: 'solid',
          disabled: fileName.length === 0,
          loading: createFile.loading,
          onClick: submit,
        },
      ],
    }"
    @close="dialogType = ''"
  >
    <template #body-content>
      <FormControl
        v-model="fileName"
        v-focus
        :label="__('Name:')"
        @keyup.enter="submit"
        @keydown="createFile.error = null"
      >
        <template #prefix>
          <component :is="fileIcon" class="size-4" />
        </template>
      </FormControl>
      <div
        v-if="createFile.error"
        class="pt-4 text-base font-sm text-ink-red-3"
      >
        {{ createFile.error.messages?.[0] || createFile.error.message }}
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from "vue"
import { Dialog, FormControl, createResource } from "frappe-ui"
import { useRoute, useRouter } from "vue-router"
import LucideFileText from "~icons/lucide/file-text"
import LucideFileSpreadsheet from "~icons/lucide/file-spreadsheet"
import LucidePresentation from "~icons/lucide/presentation"

const route = useRoute()
const router = useRouter()

const props = defineProps({
  parent: String,
  fileType: {
    type: String,
    required: true,
    validator: (value) => ["docx", "xlsx", "pptx"].includes(value),
  },
})
const emit = defineEmits(["success"])

const dialogType = defineModel()
const open = ref(true)

const fileName = ref("")

const dialogTitle = computed(() => {
  const titles = {
    docx: __("Create a Word Document"),
    xlsx: __("Create a Spreadsheet"),
    pptx: __("Create a Presentation"),
  }
  return titles[props.fileType] || __("Create a Document")
})

const fileIcon = computed(() => {
  const icons = {
    docx: LucideFileText,
    xlsx: LucideFileSpreadsheet,
    pptx: LucidePresentation,
  }
  return icons[props.fileType] || LucideFileText
})

const createFile = createResource({
  url: "drive_wopi.api.editor.create_office_file",
  onSuccess(data) {
    open.value = false
    emit("success", data)
    // Navigate to the new file to open it in Collabora
    if (data.file_id) {
      router.push({ name: "File", params: { entityName: data.file_id } })
    }
  },
})

const submit = () => {
  const title = fileName.value.trim()
  if (!title) return

  createFile.submit({
    file_type: props.fileType,
    title: title,
    parent: props.parent || null,
  })
}
</script>
