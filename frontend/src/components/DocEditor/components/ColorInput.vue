<template>
  <ColorPicker
    :model-value="value"
    @update:model-value="(color) => emit('change', color)"
  >
    <template #target="{ togglePopover }">
      <div class="flex items-stretch">
        <span class="font-medium uppercase text-gray-600">
          {{ label }}
        </span>
        <div class="relative w-full">
          <div
            :style="{
              background: value
                ? value
                : `url(/color-circle.png) center / contain`,
            }"
            class="absolute left-2 top-[6px] z-10 h-4 w-4 rounded shadow-sm cursor-pointer"
            @click="togglePopover"
          ></div>
          <Input
            type="text"
            class="rounded-md text-sm text-gray-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:focus:bg-zinc-700"
            placeholder="Set Color"
            input-class="pl-8 pr-6"
            :value="value"
            @change="
              (value) => {
                value = getRGB(value)
                emit('change', value)
              }
            "
          ></Input>
          <div
            v-show="value"
            class="absolute right-1 top-[3px] cursor-pointer p-1 text-gray-700 dark:text-zinc-300"
            @click="clearValue"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
            >
              <path
                fill="currentColor"
                d="M18.3 5.71a.996.996 0 0 0-1.41 0L12 10.59L7.11 5.7A.996.996 0 1 0 5.7 7.11L10.59 12L5.7 16.89a.996.996 0 1 0 1.41 1.41L12 13.41l4.89 4.89a.996.996 0 1 0 1.41-1.41L13.41 12l4.89-4.89c.38-.38.38-1.02 0-1.4z"
              />
            </svg>
          </div>
        </div>
      </div>
    </template>
  </ColorPicker>
</template>
<script setup lang="ts">
import { Input } from "frappe-ui"
import { getRGB } from "@/utils/helpers"
import ColorPicker from "./ColorPicker.vue"

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

const emit = defineEmits(["change"])

const clearValue = () => emit("change", null)
</script>
