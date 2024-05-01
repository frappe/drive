<template>
  <div
    class="rounded-full relative flex items-center justify-center"
    :class="[colorClasses, sizeClasses]"
  >
    <Globe v-if="props.generalAccess.public" class="h-5 w-5" />
    <Organization v-else-if="props.generalAccess.everyone" class="h-5 w-5" />
    <Lock v-else class="h-5 w-5" />
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
      }
    },
  },
  size: {
    type: String,
    default: "md",
  },
})

const colorClasses = computed(() => {
  if (props.generalAccess.public) {
    return "bg-red-100 text-red-500"
  } else if (props.generalAccess.everyone) {
    return "bg-blue-100 text-blue-500"
  }
  return "text-gray-600 bg-gray-100"
})
const sizeClasses = computed(() => {
  return {
    xs: "w-4 h-4",
    sm: "w-5 h-5",
    md: "w-6 h-6",
    lg: "w-7 h-7",
    xl: "w-8 h-8",
    "2xl": "w-10 h-10",
    "3xl": "w-11.5 h-11.5",
  }[props.size]
})
</script>
