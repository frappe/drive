<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="font-semibold text-ink-gray-9">
        {{ __("Templates") }}
      </h1>
      <Button @click="showAddDialog = true">
        <template #prefix>
          <LucidePlus class="size-4" />
        </template>
        {{ __("Add Template") }}
      </Button>
    </div>

    <div
      v-if="!templates.data?.length && templates.isFinished"
      class="w-full flex flex-col items-center justify-center my-10"
    >
      <LucideFileText class="h-7 stroke-1 text-ink-gray-5" />
      <span class="text-ink-gray-8 text-sm mt-2">No Templates</span>
    </div>

    <div
      v-else-if="templates.data?.length"
      class="flex flex-col items-start justify-start w-full rounded px-1.5"
    >
      <div
        v-for="(template, index) in templates.data"
        :key="template.name"
        class="w-full h-12 flex items-center justify-start py-3 gap-x-3"
        :class="index > 0 ? 'border-t' : ''"
        @mouseenter="hoveredRow = template.name"
        @mouseleave="hoveredRow = null"
      >
        <LucideFileText class="size-4 text-ink-gray-5 flex-shrink-0" />

        <div class="flex flex-col flex-1 min-w-0">
          <span class="text-ink-gray-8 text-sm font-medium truncate">
            {{ template.title }}
          </span>
        </div>

        <div class="flex gap-2 items-center ml-auto">
          <Button
            v-if="hoveredRow === template.name"
            variant="ghost"
            @click="editTemplate(template)"
          >
            <LucidePencil class="size-4 text-ink-gray-5" />
          </Button>
          <Button
            v-if="hoveredRow === template.name"
            variant="ghost"
            @click="confirmDelete(template)"
          >
            <LucideTrash2 class="size-4 text-red-600" />
          </Button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Template Dialog -->
    <Dialog
      v-model="showAddDialog"
      :options="{
        title: editingTemplate ? __('Edit Template') : __('Add Template'),
        size: 'xl',
        actions: [
          {
            label: editingTemplate ? __('Update') : __('Add'),
            loading: isSaving,
            disabled: !formData.title,
            onClick: saveTemplate,
            variant: 'solid',
          },
        ],
      }"
    >
      <template #body-content>
        <div class="space-y-4">
          <FormControl
            type="text"
            variant="outline"
            v-model="formData.title"
            autocomplete="off"
            :placeholder="__('Enter template title')"
            label="Title"
            :required="true"
          />
          <div class="space-y-1.5">
            <FormLabel
              :label="__('Content')"
              :required="true"
            />
            <TextEditor
              ref="textEditor"
              :content="formData.content"
              :editable="true"
              editor-class="prose-sm max-w-none min-h-[300px] max-h-[300px] overflow-y-auto px-3 py-2 border rounded"
            />
          </div>
        </div>
      </template>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog
      v-model="showDeleteDialog"
      :options="{
        title: __('Delete Template'),
        message: `Are you sure you want to delete this (${templateToDelete?.title}) template?`,
        size: 'sm',
        actions: [
          {
            label: 'Delete',
            theme: 'red',
            loading: templates.delete.loading,
            onClick: deleteTemplate,
          },
        ],
      }"
    />
  </div>
</template>

<script setup>
import { ref, reactive } from "vue"
import {
  Button,
  Dialog,
  FormLabel,
  FormControl,
  TextEditor,
  createListResource,
} from "frappe-ui"
import LucideFileText from "~icons/lucide/file-text"
import LucidePlus from "~icons/lucide/plus"
import LucidePencil from "~icons/lucide/pencil"
import LucideTrash2 from "~icons/lucide/trash-2"

const hoveredRow = ref(null)
const showAddDialog = ref(false)
const showDeleteDialog = ref(false)
const editingTemplate = ref(null)
const templateToDelete = ref(null)
const textEditor = ref(null)
const isSaving = ref(false)

const formData = reactive({
  title: "",
  content: "",
})

// Use the modern useList resource
const templates = createListResource({
  doctype: "Writer Template",
  fields: ["name", "title", "content", "creation", "modified"],
  orderBy: "modified desc",
  auto: true,
})

function editTemplate(template) {
  editingTemplate.value = template
  formData.title = template.title
  formData.content = template.content || ""
  showAddDialog.value = true
}

function closeDialog() {
  showAddDialog.value = false
  editingTemplate.value = null
  formData.title = ""
  formData.content = ""
}

async function saveTemplate() {
  if (!formData.title) return

  const htmlContent = textEditor.value?.editor?.getHTML() || ""
  isSaving.value = true

  try {
    if (editingTemplate.value) {
      // Update existing template
      await templates.setValue.submit({
        name: editingTemplate.value.name,
        title: formData.title,
        content: htmlContent,
      })
    } else {
      // Create new template
      await templates.insert.submit({
        title: formData.title,
        content: htmlContent,
      })
    }

    templates.reload()
    closeDialog()
  } catch (error) {
    console.error("Error saving template:", error)
  } finally {
    isSaving.value = false
    editingTemplate.value = null
  }
}

function confirmDelete(template) {
  templateToDelete.value = template
  console.log(template)
  showDeleteDialog.value = true
}

async function deleteTemplate() {
  if (!templateToDelete.value) return

  try {
    await templates.delete.submit(templateToDelete.value.name)
    showDeleteDialog.value = false
    templateToDelete.value = null
  } catch (error) {
    console.error("Error deleting template:", error)
  }
}
</script>
