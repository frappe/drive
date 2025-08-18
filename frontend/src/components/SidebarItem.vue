<template>
  <button
    class="flex h-10 w-full cursor-pointer items-center rounded-md duration-200 ease-in-out group transition-all"
    :class="
      isActive 
        ? 'bg-blue-600 text-white shadow-md font-semibold border border-blue-700' 
        : 'text-gray-700 hover:bg-white hover:shadow-sm hover:text-gray-900 hover:border hover:border-gray-200'
    "
    @click="handleClick"
  >
    <div
      class="flex w-full items-center justify-between duration-200 ease-in-out px-3 py-2"
    >
      <div class="flex items-center">
        <Tooltip
          :text="label"
          placement="right"
          arrow-class="fill-gray-900"
          :disabled="!isCollapsed"
        >
          <slot name="icon">
            <span class="grid h-5 w-5 flex-shrink-0 place-items-center">
              <component
                :is="icon"
                class="size-5 transition-colors"
                :class="isActive ? 'text-white font-bold' : 'text-gray-600 group-hover:text-gray-900'"
                :style="isActive ? 'font-weight: 900;' : ''"
              />
            </span>
          </slot>
        </Tooltip>
        <span
          class="flex-1 flex-shrink-0 text-[14px] duration-200 ease-in-out"
          :class="[
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-3 w-auto opacity-100',
            isActive ? 'font-semibold text-white' : 'font-medium text-gray-700 group-hover:text-gray-900'
          ]"
        >
          {{ label }}
        </span>
      </div>
      <slot name="right" />
    </div>
  </button>
</template>

<script setup>
import { Tooltip } from "frappe-ui"
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"

const route = useRoute()
const router = useRouter()
const store = useStore()

const props = defineProps({
  icon: {
    type: [Function, Object],
    default: null,
  },
  label: {
    type: String,
    default: "",
  },
  to: {
    type: [Object, String],
    default: "",
  },
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

function handleClick() {
  router.push({ path: props.to })
}

const isActive = computed(() => {
  if (!props.to) return false
  
  // Check if current route matches the target route
  const currentPath = route.path
  const targetPath = props.to
  
  // Exact match for simple routes
  if (currentPath === targetPath) return true
  
  // For breadcrumb fallback
  const first = store.state.breadcrumbs?.[0]
  if (first && (first.label === props.label || first.name === props.label)) {
    return true
  }
  
  return false
})
</script>
