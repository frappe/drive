<template>
  <div
    v-if="actionItems.length > 0"
    ref="contextMenu"
    class="w-[208px] p-1.5 absolute mt-2 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
    :style="{
      left: `${calculateX}px`,
      top: `${calculateY}px`,
      'z-index': 1000,
    }"
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
      <div v-if="item.divider">
        <hr class="my-1 bg-surface-gray-4" />
      </div>
      <button
        v-else
        class="group flex h-7 w-full items-center rounded px-2 text-base hover:bg-surface-gray-3 text-ink-gray-6"
      >
        <component
          :is="item.icon"
          class="mr-2 size-4 flex-shrink-0"
          :class="item.danger ? 'text-[#E03636]' : 'text-ink-gray-7'"
        />
        <span
          class="whitespace-nowrap"
          :class="item.danger ? 'text-ink-red-4' : 'text-ink-gray-7'"
        >
          {{ item.label }}
        </span>
      </button>
    </div>
  </div>
</template>
<script setup>
import { onBeforeUnmount, onMounted, onUpdated, ref } from "vue"
import disableScroll from "@/utils/disable-scroll"

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
  parentWidth.value = window.document.body.clientWidth
  parentHeight.value = window.document.body.clientHeight
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
