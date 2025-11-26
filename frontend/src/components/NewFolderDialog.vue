<template>
  <Dialog
    v-model="open"
    :options="{
      title: 'Create a Folder',
      size: 'xs',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          disabled: folderName.length === 0,
          loading: createFolder.loading,
          onClick: submit,
        },
      ],
    }"
    @close="dialogType = ''"
  >
    <template #body-content>
      <FormControl
        v-model="folderName"
        v-focus
        label="Name:"
        @keyup.enter="submit"
        @keydown="createFolder.error = null"
      >
        <template #prefix>
          <LucideFolderClosed class="size-4" />
        </template>
      </FormControl>
      <div
        v-if="createFolder.error"
        class="pt-4 text-base font-sm text-ink-red-3"
      >
        {{ createFolder.error.messages[0] }}
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue"
import { Dialog, createResource } from "frappe-ui"
import { useRoute } from "vue-router"

const route = useRoute()
const props = defineProps({
  parent: String,
})
const emit = defineEmits(["success"])

const dialogType = defineModel()
const open = ref(true)

const folderName = ref("")

const createFolder = createResource({
  url: "drive.api.files.create_folder",
  makeParams(title) {
    return {
      file_name: title,
      team: route.params.team,
      parent: props.parent,
    }
  },
  onSuccess(data) {
    open.value = false
    emit("success", data)
  },
})
const submit = () => createFolder.submit(folderName.value.trim())
</script>
