<template>
  <div
    v-if="actionItems.length > 0"
    ref="emptyContextMenu"
    class="bg-white rounded-lg absolute shadow-xl px-1.5 py-1 z-20 border min-w-40"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }"
  >
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      class="py-0.5"
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
      <div
        v-else
        class="h-6 px-2 hover:bg-gray-100 text-sm whitespace-nowrap cursor-pointer rounded flex justify-start items-center"
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
        <div class="text-gray-800 mr-4">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { onBeforeMount, onMounted, onUpdated, ref } from "vue"
import disableScroll from "@/utils/disable-scroll"
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
  actionItems: Array,
  event: Object,
  close: Function,
})

const emptyContextMenu = ref(null)
const parentWidth = ref(null)
const parentHeight = ref(null)
const childWidth = ref(null)
const childHeight = ref(null)

onMounted(() => {
  parentWidth.value = emptyContextMenu.value.parentElement.clientWidth
  parentHeight.value = emptyContextMenu.value.parentElement.clientHeight
  childWidth.value = emptyContextMenu.value.clientWidth
  childHeight.value = emptyContextMenu.value.clientHeight
  calculateY()
  calculateX()
  disableScroll.on()
})

onUpdated(() => {
  calculateY()
  calculateX()
})

onBeforeMount(() => {
  disableScroll.off()
})

function calculateY() {
  if (props.event.y >= parentHeight.value - childHeight.value) {
    return (emptyContextMenu.value.style.top =
      props.event.y - childHeight.value + "px")
  } else {
    return (emptyContextMenu.value.style.top = props.event.y + "px")
  }
}
function calculateX() {
  if (props.event.x >= parentWidth.value - childWidth.value) {
    return (emptyContextMenu.value.style.left =
      props.event.x - childWidth.value + "px")
  } else {
    return (emptyContextMenu.value.style.left = props.event.x + "px")
  }
}
</script>
<style>
.disable-scroll {
  overflow: hidden;
}
</style>
