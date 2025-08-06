<template>
  <Dialog
    v-model="open"
    @close="dialogType = 'l'"
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
  >
    <template #body-content>
      <FormControl
        v-focus
        v-model="folderName"
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
        This folder already exists.
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue"
import store from "@/store"
import { Dialog, createResource } from "frappe-ui"
import { useRoute } from "vue-router"
import { allFolders } from "@/resources/files"

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
      title,
      team: route.params.team,
      parent: props.parent,
      personal: store.state.breadcrumbs[0].name == "Home" ? 1 : 0,
    }
  },
  validate(params) {
    if (!params?.title) {
      return "Folder name is required"
    }
  },
  onSuccess(data) {
    open.value = false
    emit("success", data)
    allFolders.fetch()
  },
})
const submit = () => createFolder.submit(folderName.value.trim())
</script>
