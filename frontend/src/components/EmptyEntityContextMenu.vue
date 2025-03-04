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
<script>
import disableScroll from "../utils/disable-scroll"
import { FeatherIcon } from "frappe-ui"

export default {
  name: "EmptyEntityContext",
  props: {
    actionItems: {
      type: Array,
      default: null,
    },
    event: {
      type: Object,
      default: null,
    },
    close: {
      type: Function,
      default: null,
    },
  },
  data() {
    return {
      FeatherIcon,
      parentWidth: null,
      parentHeight: null,
      childWidth: null,
      childHeight: null,
    }
  },
  mounted() {
    this.parentWidth = this.$refs.emptyContextMenu.parentElement.clientWidth
    this.parentHeight = this.$refs.emptyContextMenu.parentElement.clientHeight
    this.childWidth = this.$refs.emptyContextMenu.clientWidth
    this.childHeight = this.$refs.emptyContextMenu.clientHeight
    this.calculateY()
    this.calculateX()
    disableScroll.on()
  },
  updated() {
    this.calculateY()
    this.calculateX()
  },
  beforeUnmount() {
    disableScroll.off()
  },
  methods: {
    disableScroll() {
      document.querySelector("#currentPage").classList.add("disable-scroll")
    },
    enableScroll() {
      document.querySelector("#currentPage").classList.remove("disable-scroll")
    },
    calculateY() {
      if (this.event.y >= this.parentHeight - this.childHeight) {
        return (this.$refs.emptyContextMenu.style.top =
          this.event.y - this.childHeight + "px")
      } else {
        return (this.$refs.emptyContextMenu.style.top = this.event.y + "px")
      }
    },
    calculateX() {
      if (this.event.x >= this.parentWidth - this.childWidth) {
        return (this.$refs.emptyContextMenu.style.left =
          this.event.x - this.childWidth + "px")
      } else {
        return (this.$refs.emptyContextMenu.style.left = this.event.x + "px")
      }
    },
  },
}
</script>
<style>
.disable-scroll {
  overflow: hidden;
}
</style>
