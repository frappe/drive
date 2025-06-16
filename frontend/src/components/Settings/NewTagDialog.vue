<template>
  <Dialog
    v-model="open"
    :options="{ title: 'New Tag', size: 'sm' }"
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
          :placeholder="placeholder"
          label="Title"
          @keyup.enter="submitTag"
        />
      </div>
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
import { Button, Input, Dialog, createResource } from "frappe-ui"
import TagColorInput from "@/components/TagColorInput.vue"
import { getRandomColor } from "@/utils/random-color"
import { ref, computed } from "vue"
import { useFocus } from "@vueuse/core"

const inputElem = ref()
const { focused } = useFocus(inputElem, { initialValue: true })

const selectedColor = ref(getRandomColor())
const tagTitle = ref("")
const placeholder = getRandomPlaceholder()

const emit = defineEmits(["update:modelValue", "success"])
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: false,
    default: true,
  },
})

const open = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit("update:modelValue", value)
  },
})

function submitTag() {
  newTag.submit({
    title: tagTitle.value.trim(),
    color: selectedColor.value,
  })
}

function getRandomPlaceholder() {
  const fileTags = [
    "Marketing",
    "Draft",
    "Confidential",
    "Public",
    "Webinar",
    "Approved",
    "Draft",
    "Invoice",
  ]
  return fileTags[Math.floor(Math.random() * fileTags.length)]
}

const newTag = createResource({
  url: "drive.api.tags.create_tag",
  onSuccess() {
    emit("success")
    emit("update:modelValue", false)
  },
  onError(error) {
    if (error.messages) {
      console.log(error.messages)
    }
  },
})
</script>
