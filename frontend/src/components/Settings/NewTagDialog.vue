<template>
  <Dialog
    v-model="open"
    :options="{ title: __('New Tag'), size: 'sm' }"
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
          :label="__('Title')"
          @keyup.enter="submitTag"
        />
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full !bg-[#0149C1] text-white hover:!opacity-90"
        @click="submitTag"
      >
        {{ __('Confirm') }}
      </Button>
    </template>
  </Dialog>
</template>
<script setup>
import TagColorInput from "@/components/TagColorInput.vue"
import { getRandomColor } from "@/utils/random-color"
import { useFocus } from "@vueuse/core"
import { Button, Dialog, Input, createResource } from "frappe-ui"
import { computed, ref } from "vue"

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
    __("Marketing"),
    __("Draft"),
    __("Confidential"),
    __("Public"),
    __("Webinar"),
    __("Approved"),
    __("Draft"),
    __("Invoice"),
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
