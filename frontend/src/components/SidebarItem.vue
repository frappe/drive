<template>
  <button
    class="flex h-10 w-full cursor-pointer items-center rounded-md duration-200 ease-in-out group transition-all"
    :class="
      isActive 
        ? 'bg-[#d4e1f9] text-[#0149C1] shadow-sm font-semibold border border-blue-200' 
        : 'text-black hover:shadow-sm hover:border hover:border-gray-150'
    "
    @click="handleClick"
  >
    <div
      class="flex w-full items-center justify-between duration-200 ease-in-out px-3 py-2"
    >
      <div class="flex items-center justify-start">
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
                :class="isActive ? 'text-blue-700 font-bold' : 'text-black'"
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
            isActive ? 'font-semibold text-blue-700' : 'font-medium text-black'
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
