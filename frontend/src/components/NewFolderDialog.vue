<template>
  <Dialog
    v-model="open"
    :options="{
      title: 'Create new folder',
      size: 'xs',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          disabled: folderName.length === 0,
          loading: submit.loading,
          onClick: submit,
        },
      ],
    }"
  >
    <template #body-content>
      <p class="text-ink-gray-5 text-sm mb-2">Folder name:</p>
      <TextInput
        ref="my-input"
        v-model="folderName"
        @keyup.enter="submit"
        @keydown="createFolder.error = null"
      >
        <template #prefix>
          <LucideFolderClosed class="size-4" />
        </template>
      </TextInput>
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
import { ref, computed, useTemplateRef, watch } from "vue"
import store from "@/store"
import { Dialog, TextInput, createResource } from "frappe-ui"
import { useRoute } from "vue-router"
import { allFolders } from "../resources/files"

const route = useRoute()
const props = defineProps({
  modelValue: String,
  parent: String,
})
const emit = defineEmits(["update:modelValue", "success", "mutate"])
const folderName = ref("")
const text = useTemplateRef("my-input")
watch(text, (val) => {
  val.el.focus()
})

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
    folderName.value = ""
    allFolders.fetch()
    emit("success", data)
  },
})

const open = computed({
  get: () => {
    return props.modelValue === "f"
  },
  set: (value) => {
    if (!value) {
      emit("update:modelValue", "")
      folderName.value = ""
    }
  },
})

const submit = () => createFolder.submit(folderName.value.trim())
</script>
