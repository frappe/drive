<template>
  <Dialog
    v-model="open"
    :options="{
      title: 'New Presentation',
      size: 'xs',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          disabled: presentationName.length === 0,
          loading: createPresentation.loading,
          onClick: submit,
        },
      ],
    }"
    @close="dialogType = ''"
  >
    <template #body-content>
      <FormControl
        v-model="presentationName"
        v-focus
        label="Name:"
        @keyup.enter="submit"
        @keydown="createPresentation.error = null"
      >
        <template #prefix>
          <LucideGalleryVerticalEnd class="size-4" />
        </template>
      </FormControl>

      <div
        v-if="createPresentation.error"
        class="pt-4 text-base font-sm text-ink-red-3"
      >
        {{ createFolder.error.messages[0] }}
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue"
import { Dialog } from "frappe-ui"
import { createPresentation } from "@/resources/files"
import { useStore } from "vuex"
import { useRoute } from "vue-router"

const props = defineProps({
  parent: String,
})
const route = useRoute()
const store = useStore()
const emit = defineEmits(["success"])

const dialogType = defineModel()
const open = ref(true)

const presentationName = ref("")
const submit = async () => {
  const data = await createPresentation.submit({
    parent: props.parent,
    title: presentationName.value.trim(),
    team: route.params.team,
  })
  console.log(data)
  emit("success", data)
}
</script>
