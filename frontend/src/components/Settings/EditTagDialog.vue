<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Edit Tag', size: 'sm' }"
  >
    <template #body-content>
      <div class="flex flex-col items-stretch justify- gap-y-4">
        <TagColorInput
          class="mt-0.5 mb-1"
          :value="selectedColor"
          @change="(newVal) => (selectedColor = newVal)"
        />
        <Input
          ref="inputElem"
          v-model="tagTitle"
          type="text"
          clas="w-full"
          :placeholder="props.tag.title"
          label="Title"
          @keyup.enter="submitTag"
        />
      </div>
      <ErrorMessage
        class="mt-2"
        :message="errorMessage"
      />
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full"
        @click="submitTag"
      >
        Confirm
      </Button>
    </template>
  </Dialog>
</template>
<script setup>
import { Button, Input, Dialog, createResource, ErrorMessage } from "frappe-ui"
import TagColorInput from "@/components/TagColorInput.vue"
import { ref, computed } from "vue"
import { useFocus } from "@vueuse/core"

const inputElem = ref()
const { focused } = useFocus(inputElem, { initialValue: true })

const props = defineProps({
  tag: {
    type: Object,
    required: true,
  },
  modelValue: {
    type: Boolean,
    required: false,
    default: true,
  },
})

const selectedColor = ref(props.tag.color)
const tagTitle = ref(props.tag.title)
const errorMessage = ref("")
const emit = defineEmits(["update:modelValue", "success"])

const open = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit("update:modelValue", value)
  },
})

function submitTag() {
  if (tagTitle.value.length) {
    editTag.submit({
      tag: props.tag.name,
      title: tagTitle.value.trim(),
      color: selectedColor.value,
    })
  }
}

const editTag = createResource({
  url: "drive.api.tags.edit_tag",
  onSuccess() {
    emit("success")
    emit("update:modelValue", false)
  },
  onError(error) {
    if (error.messages) {
      errorMessage.value = error.messages.join("\n")
    } else {
      errorMessage.value = error.message
    }
  },
})
</script>
