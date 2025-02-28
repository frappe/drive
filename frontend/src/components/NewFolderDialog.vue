<template>
  <Dialog v-model="open" :options="{ title: 'New Folder', size: 'xs' }">
    <template #body-content>
      <Input
        ref="input"
        v-model="folderName"
        placeholder="folder name..."
        type="text"
        @keyup.enter="submit"
        @keydown="createFolder.error = null"
      />
      <div
        v-if="createFolder.error"
        class="pt-4 text-base font-sm text-red-500"
      >
        This folder already exists.
      </div>
      <div class="flex" :class="createFolder.error ? 'mt-5' : 'mt-8'">
        <Button
          variant="solid"
          class="w-full"
          :loading="createFolder.loading"
          @click="submit"
        >
          Create
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from "vue"
import store from "@/store"
import { Dialog, Input, createResource } from "frappe-ui"
import { useRoute } from "vue-router"
const route = useRoute()
const props = defineProps({
  modelValue: String,
  parent: String,
})
const emit = defineEmits(["update:modelValue", "success", "mutate"])
const folderName = ref("")

const createFolder = createResource({
  url: "drive.api.files.create_folder",
  makeParams(title) {
    return {
      title,
      team: route.params.team,
      parent: props.parent,
      personal: store.state.breadcrumbs[0].label == "Home" ? 1 : 0,
    }
  },
  validate(params) {
    if (!params?.title) {
      return "Folder name is required"
    }
  },
  onSuccess(data) {
    folderName.value = ""
    emit("success", data)
  },
})

const open = computed({
  get: () => {
    return props.modelValue === "f"
  },
  set: (value) => {
    emit("update:modelValue", value)
    if (!value) folderName.value = ""
  },
})

const submit = () => createFolder.submit(folderName.value.trim())
</script>
