<template>
  <Dialog v-model="open" :options="{ title: 'New Link', size: 'xs' }">
    <template #body-content>
      <TextInput
        ref="input"
        class="pb-2"
        v-model="title"
        placeholder="Link name"
        type="text"
        @keydown="createLink.error = null"
      />
      <TextInput
        ref="input"
        class="pt-2"
        v-model="link"
        placeholder="URL"
        type="url"
        @keydown.enter="createLink.submit"
        @keydown="createLink.error = null"
      />
      <div v-if="createLink.error" class="pt-4 text-base font-sm text-red-500">
        This file already exists.
      </div>
      <div class="flex" :class="createLink.error ? 'mt-5' : 'mt-8'">
        <Button
          variant="solid"
          class="w-full"
          :loading="createLink.loading"
          @click="createLink.submit"
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
import { Dialog, TextInput, createResource } from "frappe-ui"
import { useRoute } from "vue-router"
const route = useRoute()
const props = defineProps({
  modelValue: String,
  parent: String,
  link: String,
})
const emit = defineEmits(["update:modelValue", "success"])

const title = ref("")
const link = ref(props.link)

const createLink = createResource({
  url: "drive.api.files.create_link",
  makeParams() {
    return {
      title: title.value.trim(),
      link: link.value.trim(),
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
    title.value = ""
    link.value = ""
    emit("success", data)
  },
})

const open = computed({
  get: () => {
    return props.modelValue === "l"
  },
  set: (value) => {
    emit("update:modelValue", value)
    if (!value) title.value = ""
  },
})
</script>
