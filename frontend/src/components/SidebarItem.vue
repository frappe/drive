<template>
  <button
    class="flex h-7 w-full cursor-pointer items-center rounded text-ink-gray-7 active:bg-surface-selected hover:bg-surface-gray-2"
    @click="handleClick"
  >
    <div
      class="flex w-full items-center justify-between duration-300 ease-in-out p-2"
    >
      <div class="flex items-center">
        <Tooltip
          :text="__(label)"
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
          {{ __(label) }}
        </span>
      </div>
      <slot name="right" />
    </div>
  </button>
</template>

<script setup>
import { Tooltip } from "frappe-ui"
import { useRouter } from "vue-router"

const router = useRouter()

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
</script>
