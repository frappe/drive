<template>
  <ColorPicker
    :model-value="value"
    @update:model-value="(value) => emit('change', value)"
  >
    <template #target="{ togglePopover }">
      <span class="mb-2 block text-sm leading-4 text-ink-gray-7"> Color </span>
      <div class="flex items-stretch">
        <div class="relative w-full">
          <div
            class="absolute left-2 top-[6px] z-10 size-4 rounded shadow-sm cursor-pointer"
            @click="togglePopover"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <circle
                r="4.5"
                cx="8"
                cy="8"
                :fill="value"
                :stroke="value"
                stroke-width="3"
              />
            </svg>
          </div>
          <Input
            type="text"
            class="rounded-md text-sm text-ink-gray-7 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:focus:bg-zinc-700"
            placeholder="Set Color"
            input-class="pl-8 pr-6"
            :value="value"
            @change="
              (value) => {
                emit('change', value)
              }
            "
          />
        </div>
      </div>
    </template>
  </ColorPicker>
</template>
<script setup lang="ts">
import { Input } from "frappe-ui"
import ColorPicker from "@/components/DocEditor/components/ColorPicker.vue"
const emit = defineEmits(["change"])

defineProps({
  value: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: "",
  },
})
</script>
