<template>
  <div
    class="rounded-full relative flex items-center justify-center"
    :class="[
      colorClasses,
      sizeClasses,
      { 'opacity-50 cursor-not-allowed': props.disabled },
    ]"
  >
    <Globe
      v-if="props.generalAccess.public"
      :class="size == 'sm' ? 'h-[90%] w-[90%]' : 'h-[70%] w-[70%]'"
    />
    <Organization
      v-else-if="props.generalAccess.everyone"
      :class="size == 'sm' ? 'h-[80%] w-[80%]' : 'h-[70%] w-[70%]'"
    />
    <Lock
      v-else
      class=""
      :class="size == 'sm' ? 'h-[80%] w-[80%]' : 'h-[65%] w-[65%]'"
    />
  </div>
</template>
<script setup>
import Lock from "@/components/EspressoIcons/Lock.vue"
import Organization from "./EspressoIcons/Organization.vue"
import Globe from "./EspressoIcons/Globe.vue"
import { computed } from "vue"

const props = defineProps({
  generalAccess: {
    type: Object,
    default() {
      return {
        read: 0,
        public: 0,
        everyone: 0,
      }
    },
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
    return "bg-gray-300 text-gray-500"
  } else if (props.generalAccess.public) {
    return "bg-red-100 text-red-500"
  } else if (props.generalAccess.everyone) {
    return "bg-blue-100 text-blue-500"
  }
  return "text-gray-600 bg-gray-100"
})

const sizeClasses = computed(() => {
  return {
    xs: "w-3 h-3",
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-7 h-7",
    xl: "w-8 h-8",
    "2xl": "w-10 h-10",
    "3xl": "w-11.5 h-11.5",
  }[props.size]
})
</script>
