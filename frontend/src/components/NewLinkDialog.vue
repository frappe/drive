<template>
  <Dialog
    v-model="open"
    @close="dialogType = ''"
    :options="{
      title: 'New Link',
      size: 'xs',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          loading: createLink.loading,
          onClick: createLink.submit,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-focus
          v-model="title"
          label="Link name"
          type="text"
          @keydown="createLink.error = null"
        />
        <FormControl
          v-model="link"
          label="URL"
          type="url"
          @keydown.enter="createLink.submit"
          @keydown="createLink.error = null"
        />
      </div>
      <div
        v-if="createLink.error"
        class="pt-4 text-base font-sm text-ink-red-3"
      >
        This link already exists.
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue"
import store from "@/store"
import { Dialog, TextInput, createResource } from "frappe-ui"
import { useRoute } from "vue-router"

const route = useRoute()

const props = defineProps({
  parent: String,
})
const emit = defineEmits(["success"])

const open = ref(true)
const dialogType = defineModel()

const title = ref("")
const link = ref(localStorage.getItem("prevClip") || "")

const createLink = createResource({
  url: "drive.api.files.create_link",
  makeParams: () => ({
    title: title.value.trim(),
    link: link.value.trim(),
    team: route.params.team,
    parent: props.parent,
    personal: store.state.breadcrumbs[0].name == "Home" ? 1 : 0,
  }),
  validate(params) {
    if (!params?.title) {
      return "Link name is required"
    }
  },
  onSuccess(data) {
    open.value = false
    title.value = ""
    link.value = ""
    emit("success", data)
  },
})
</script>
