<template>
  <Dialog v-model="open" :options="{ title: 'none', size: '4xl' }">
    <template #body>
      <div class="px-4 pb-6 pt-5 sm:px-6">
        <div class="w-full mb-4">
          <h3 class="text-2xl font-semibold leading-6 text-gray-900">
            snapshotData.message
          </h3>
          <span class="text-gray-700 text-base"
            >Created on {{ snapshotData.date }} by
            {{ snapshotData.author }}</span
          >
          <Button
            icon="x"
            :variant="'ghost'"
            class="absolute top-5 right-5"
            @click="$emit('update:modelValue', false)"
          ></Button>
        </div>
        <div class="max-h-[74vh] overflow-y-auto mb-4">
          <PreviewEditor
            v-if="snapshotData"
            :yjs-update="snapshotData.snapshot"
          />
        </div>
        <Button class="w-full" :variant="'solid'">Restore</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  ref,
  computed,
  defineEmits,
  defineProps,
  onMounted,
  onBeforeUnmount,
} from "vue"
import { Dialog, Button, FeatherIcon } from "frappe-ui"
import PreviewEditor from "../PreviewEditor.vue"
import { useDateFormat } from "@vueuse/core"

defineOptions({
  inheritAttrs: false,
})

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

const loading = ref(false)

onBeforeUnmount(() => {
  emit("success")
})
</script>
