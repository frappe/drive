<template>
  <Dialog v-model="open" :options="{ title: 'none', size: '4xl' }">
    <template #body>
      <div v-if="snapshotData" class="px-4 pb-6 pt-5 sm:px-6">
        <div class="w-full mb-4">
          <h3 class="text-2xl font-semibold leading-6 text-gray-900">
            {{ snapshotData.snapshot_message }}
          </h3>
          <span class="text-gray-700 text-sm"
            >Created on {{ snapshotData.creation }} by
            {{ snapshotData.owner }}</span
          >
          <Button
            icon="x"
            :variant="'ghost'"
            class="absolute top-5 right-5"
            @click="$emit('update:modelValue', false)"
          ></Button>
        </div>
        <div class="mb-4">
          <PreviewEditor
            v-if="snapshotData"
            class="border h-[68vh] rounded-md overflow-y-auto"
            :yjs-update="encodeStateAsUpdate(snapshotData.snapshot_data)"
          />
        </div>
        <div class="flex">
          <Button class="ml-auto" :variant="'solid'" @click="applySnapshot"
            >Restore</Button
          >
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  inject,
  computed,
  defineEmits,
  defineProps,
  onMounted,
  onBeforeUnmount,
} from "vue"
import { Dialog, Button, Avatar } from "frappe-ui"
import PreviewEditor from "../PreviewEditor.vue"
import { encodeStateAsUpdate } from "yjs"

defineOptions({
  inheritAttrs: false,
})
const emitter = inject("emitter")
// Define props
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  snapshotData: {
    type: Object,
    required: true,
  },
})
const emit = defineEmits(["update:modelValue", "success"])

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
})

const applySnapshot = () => {
  emit("success", props.snapshotData)
  emit("update:modelValue", false)
}
onMounted(() => {
  emitter.emit("forceHideBubbleMenu", true)
})
onBeforeUnmount(() => {
  emitter.emit("forceHideBubbleMenu", false)
})
</script>
