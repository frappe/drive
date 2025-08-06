<template>
  <Dialog
    v-model="open"
    @close="dialogType = ''"
    :options="{
      title: 'Rename',
      size: 'xs',
      actions: [
        {
          label: 'Confirm',
          variant: 'solid',
          disabled: !newTitle || newTitle === entity.title,
          onClick: submit,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex gap-3">
        <FormControl
          v-model="newTitle"
          v-focus
          class="grow"
          type="text"
          @keyup.enter="submit"
        />
        <FormControl
          disabled
          v-if="file_ext"
          v-model="file_ext"
          class="flex-1"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue"
import { Dialog } from "frappe-ui"
import { rename } from "@/resources/files"

const props = defineProps({ entity: Object, modelValue: String })
const emit = defineEmits(["update:modelValue", "success"])
const dialogType = defineModel()
const open = ref(true)

const newTitle = ref("")
const file_ext = ref("")

if (props.entity.is_group || props.entity.document) {
  newTitle.value = props.entity.title
} else {
  const parts = props.entity.title.split(".")
  if (parts.length > 1) {
    newTitle.value = parts.slice(0, -1).join(".")
    file_ext.value = parts[parts.length - 1]
  } else {
    newTitle.value = parts[0]
  }
}

const submit = () => {
  const formattedTitle =
    newTitle.value + (file_ext.value ? "." + file_ext.value : "")
  rename.submit({
    entity_name: props.entity.name,
    new_title: formattedTitle,
  })
  emit("success", {
    name: props.entity.name,
    title: formattedTitle,
  })
}
</script>
