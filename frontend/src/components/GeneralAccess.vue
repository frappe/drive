<template>
  <div
    class="rounded-full relative flex items-center justify-center"
    :class="[
      colorClasses,
      sizeClasses,
      { 'opacity-50 cursor-not-allowed': props.disabled },
    ]"
  >
    <LucideGlobe2
      v-if="accessType === 'public'"
      :class="size == 'md' ? 'h-[90%] w-[90%]' : 'h-[70%] w-[70%]'"
    />
    <LucideBuilding
      v-else-if="accessType === 'team'"
      :class="size == 'sm' ? 'h-[90%] w-[90%]' : 'h-[70%] w-[70%]'"
    />
    <LucideLock
      v-else
      class=""
      :class="size == 'md' ? 'h-[80%] w-[80%]' : 'h-[65%] w-[65%]'"
    />
  </div>
</template>
<script setup>
import { computed } from "vue"

const props = defineProps({
  accessType: {
    type: String,
    default: "",
  },
  size: {
    type: String,
    default: "md",
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const colorClasses = computed(() => {
  if (props.disabled) {
    return "bg-surface-gray-4 text-ink-gray-4"
  } else if (props.accessType === "team") {
    return "bg-surface-blue-2 text-ink-blue-2"
  } else if (props.accessType === "public") {
    return "bg-surface-red-2 text-ink-red-3"
  }
  return "text-ink-gray-7 bg-surface-gray-4"
})

const sizeClasses = computed(() => {
  return {
    xs: "w-3 h-3",
    sm: "size-4",
    md: "w-6 h-6",
    lg: "w-7 h-7",
    xl: "w-8 h-8",
    "2xl": "w-10 h-10",
    "3xl": "w-11.5 h-11.5",
  }[props.size]
})
</script>
