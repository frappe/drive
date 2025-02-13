<template>
  <Dialog v-model="open" :options="{ title: 'Create a Folder', size: 'xs' }">
    <template #body-content>
      <Input
        ref="input"
        v-model="folderName"
        placeholder="folder name..."
        type="text"
        @keyup.enter="submit"
      />
      <div class="flex mt-8">
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
      personal: store.state.breadcrumbs[0].label == "My Files" ? 1 : 0,
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
