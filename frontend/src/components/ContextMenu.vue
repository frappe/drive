<template>
  <div
    v-if="actionItems.length > 0"
    ref="contextMenu"
    class="p-1.5 absolute mt-2 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }"
  >
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      @click="
        () => {
          item.handler()
          close()
        }
      "
    >
      <div v-if="item.label === 'Divider'">
        <hr />
      </div>
      <button
        v-else
        class="group flex h-7 w-full items-center rounded px-2 text-base hover:bg-surface-gray-3 text-ink-gray-6"
        @click="item.onClick"
      >
        <FeatherIcon
          v-if="item.icon && typeof item.icon === 'string'"
          :name="item.icon"
          class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-6"
          aria-hidden="true"
        />
        <component
          :is="item.icon"
          v-else-if="item.icon"
          class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-6"
        />
        <span class="whitespace-nowrap text-ink-gray-7">
          {{ item.label }}
        </span>
      </button>
      <!-- <div
        v-else
        class="group flex h-7 w-full items-center rounded px-2 text-base text-ink-gray-6"
      >
        <FeatherIcon
          v-if="item.icon && typeof item.icon === 'string'"
          :name="item.icon"
          class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-6"
          aria-hidden="true"
        />
        <component
          v-else
          class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-6"
          :is="item.icon"
        />
        <div>{{ item.label }}</div>
      </div> -->
    </div>
  </div>
</template>
<script setup>
import { onBeforeUnmount, onMounted, onUpdated, ref } from "vue"
import disableScroll from "@/utils/disable-scroll"
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
  actionItems: Array,
  event: Object,
  close: Function,
})

const contextMenu = ref(null)
const parentWidth = ref(null)
const parentHeight = ref(null)
const childWidth = ref(null)
const childHeight = ref(null)

onMounted(() => {
  parentWidth.value = contextMenu.value.parentElement.clientWidth
  parentHeight.value = contextMenu.value.parentElement.clientHeight
  childWidth.value = contextMenu.value.clientWidth
  childHeight.value = contextMenu.value.clientHeight
  calculateY()
  calculateX()
  disableScroll.on()
})

onUpdated(() => {
  calculateY()
  calculateX()
})

onBeforeUnmount(() => {
  disableScroll.off()
})

function calculateY() {
  if (props.event.y >= parentHeight.value - childHeight.value) {
    return (contextMenu.value.style.top =
      props.event.y - childHeight.value + "px")
  } else {
    return (contextMenu.value.style.top = props.event.y + "px")
  }
}
function calculateX() {
  if (props.event.x >= parentWidth.value - childWidth.value) {
    return (contextMenu.value.style.left =
      props.event.x - childWidth.value + "px")
  } else {
    return (contextMenu.value.style.left = props.event.x + "px")
  }
}
</script>
<style>
.disable-scroll {
  overflow: hidden;
}
</style>
