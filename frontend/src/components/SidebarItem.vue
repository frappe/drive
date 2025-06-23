<template>
  <button
    class="flex h-7 w-full cursor-pointer items-center rounded text-ink-gray-7 duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-outline-gray-3"
    :class="
      isActive ? ' bg-surface-selected shadow-sm' : 'hover:bg-surface-gray-2'
    "
    @click="handleClick"
  >
    <div
      class="flex w-full items-center justify-between duration-300 ease-in-out p-2"
    >
      <div class="flex items-center">
        <Tooltip
          :text="label"
          placement="right"
          arrow-class="fill-gray-900"
          :disabled="!isCollapsed"
        >
          <slot name="icon">
            <span class="grid h-4.5 w-4.5 flex-shrink-0 place-items-center">
              <component
                :is="icon"
                class="size-4 text-ink-gray-7"
              />
            </span>
          </slot>
        </Tooltip>
        <span
          class="flex-1 flex-shrink-0 text-sm duration-300 ease-in-out"
          :class="[
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100',
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
import { useStore } from "vuex"
import { useRouter } from "vue-router"

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

let isActive = computed(() => {
  const first = store.state.breadcrumbs[0]
  return first.label === props.label || first.name === props.label
})
</script>
