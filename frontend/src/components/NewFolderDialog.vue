<template>
  <Dialog v-model="open" :options="{ title: 'New Folder', size: 'xs' }">
    <template #body-content>
      <Input
        ref="input"
        v-model="folderName"
        placeholder="New folder"
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
import { Dialog, Input, createResource } from "frappe-ui"

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
      parent: props.parent,
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
