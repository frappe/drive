<template>
  <Dialog
    v-model="open"
    :options="{ title: __('New Link'), size: 'xs' }"
  >
    <template #body-content>
      <TextInput
        ref="input"
        v-model="title"
        class="pb-2"
        :placeholder="__('Link name')"
        type="text"
        @keydown="createLink.error = null"
      />
      <TextInput
        ref="input"
        v-model="link"
        class="pt-2"
        :placeholder="__('URL')"
        type="url"
        @keydown.enter="createLink.submit"
        @keydown="createLink.error = null"
      />
      <div
        v-if="createLink.error"
        class="pt-4 text-base font-sm text-ink-red-3"
      >
        {{ __("This file already exists.") }}
      </div>
      <div
        class="flex"
        :class="createLink.error ? 'mt-5' : 'mt-8'"
      >
        <Button
          variant="solid"
          class="w-full !bg-[#0149C1] text-white hover:!opacity-90"
          :loading="createLink.loading"
          @click="createLink.submit"
        >
          {{ __("Create") }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import store from "@/store"
import { Dialog, TextInput, createResource } from "frappe-ui"
import { computed, ref } from "vue"
import { useRoute } from "vue-router"
const route = useRoute()
const props = defineProps({
  modelValue: String,
  parent: String,
})
const emit = defineEmits(["update:modelValue", "success"])

const title = ref("")
const link = ref(localStorage.getItem("prevClip") || "")

const createLink = createResource({
  url: "drive.api.files.create_link",
  makeParams() {
    return {
      title: title.value.trim(),
      link: link.value.trim(),
      team: route.params.team,
      parent: props.parent,
      personal: store.state.breadcrumbs[0].name == "Home" ? 1 : 0,
    }
  },
  validate(params) {
    if (!params?.title) {
      return __("Link name is required")
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
