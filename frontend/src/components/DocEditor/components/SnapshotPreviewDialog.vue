<template>
  <Dialog
    v-model="open"
    :options="{ title: 'none', size: '4xl' }"
  >
    <template #body>
      <div
        v-if="snapshotData"
        class="px-4 pb-6 pt-5 sm:px-6"
      >
        <div class="w-full mb-4">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ snapshotData.snapshot_message }}
          </h3>
          <div class="flex items-center justify-start mt-1 mb-4">
            <span class="text-ink-gray-7 text-sm"
              >Created on {{ snapshotData.creation }} by
              {{ snapshotData.owner }}</span
            >
            <div
              class="ml-auto flex items-center justify-end rounded cursor-pointer hover:bg-surface-gray-3 pl-2 pr-1 py-1.5"
            >
              <span class="font-medium text-ink-gray-8 text-sm mr-2"
                >Highlight changes</span
              >
              <Switch v-model="showChanges" />
            </div>
          </div>
          <Button
            icon="x"
            :variant="'ghost'"
            class="absolute top-3 right-3"
            @click="$emit('update:modelValue', false)"
          />
        </div>
        <div class="mb-3">
          <PreviewEditor
            v-if="snapshotData"
            :show-changes="showChanges"
            class="border h-[68vh] rounded-md overflow-y-auto"
            :yjs-update="encodeStateAsUpdate(snapshotData.snapshot_data)"
          />
        </div>
        <div class="flex">
          <Button
            class="ml-auto"
            :variant="'solid'"
            @click="applySnapshot"
          >
            Restore
          </Button>
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
  ref,
} from "vue"
import { Dialog, Button, Switch } from "frappe-ui"
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

const showChanges = ref(false)
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
