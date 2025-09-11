<template>
  <div class="block w-full">
    <div
      class="flex items-center rounded-md p-2 ps-4 text-base md:px-5 gap-2.5"
      :class="classes"
    >
      <component
        :is="icon ? icon : LucideInfo"
        class="size-4 text-ink-gray-6"
      />
      <div class="flex items-center justify-between flex-1">
        <slot>
          <h3
            class="text-lg font-medium text-ink-gray-9"
            v-if="title"
          >
            {{ title }}
          </h3>
        </slot>
        <div class="flex gap-2">
          <slot name="actions"></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import LucideInfo from "~icons/lucide/info"

export interface AlertProps {
  title?: string
  type?: "warning"
  icon?: any
}

const props = withDefaults(defineProps<AlertProps>(), {
  type: "warning",
})

const classes = computed(() => {
  return {
    info: "text-ink-gray-7 bg-surface-gray-1 border-outline-gray-1 rounded",
    warning: "text-ink-gray-7 bg-surface-blue-1",
  }[props.type]
})
</script>
