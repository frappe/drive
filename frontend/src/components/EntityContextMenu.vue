<template>
  <div
    v-if="actionItems.length > 0"
    ref="contextMenu"
    class="bg-white rounded-lg absolute shadow-xl px-1.5 py-1 z-20 min-w-40"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }"
  >
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      @click="
        () => {
          if (item.onClick) {
            item.onClick()
            close()
          }
        }
      "
    >
      <ColorPopover v-if="item.label === 'Color'" :entity-name="entityName" />
      <div
        v-else
        class="h-7 px-2 hover:bg-gray-100 text-sm cursor-pointer rounded flex justify-start items-center"
      >
        <FeatherIcon
          v-if="typeof item.icon === 'string'"
          :name="item.icon"
          class="h-4 w-4 mr-2"
          :class="[
            item.danger ? 'text-red-500' : '',
            item.label === 'Unfavourite' ? 'fill-amber-400 text-amber-400' : '',
          ]"
        />
        <component
          :is="item.icon"
          v-else
          class="h-4 w-auto mr-2 text-gray-800"
          :class="[item.danger ? 'text-red-500' : '']"
        />
        <div
          class="text-gray-800 mr-4"
          :class="[item.danger ? 'text-red-500' : '']"
        >
          {{ item.label }}
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from "frappe-ui"
import disableScroll from "../utils/disable-scroll"
import ColorPopover from "@/components/ColorPopover.vue"

export default {
  name: "EntityContextMenu",
  components: { FeatherIcon, ColorPopover },
  props: {
    entityName: {
      type: String,
      default: null,
    },
    actionItems: {
      type: Array,
      default: null,
    },
    entityContext: {
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
      parentWidth: null,
      parentHeight: null,
      childWidth: null,
      childHeight: null,
    }
  },
  mounted() {
    this.parentWidth = this.$refs.contextMenu.parentElement.clientWidth
    this.parentHeight = this.$refs.contextMenu.parentElement.clientHeight
    this.childWidth = this.$refs.contextMenu.clientWidth
    this.childHeight = this.$refs.contextMenu.clientHeight
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
      if (this.entityContext.y >= this.parentHeight - this.childHeight) {
        return (this.$refs.contextMenu.style.top =
          this.entityContext.y - this.childHeight + "px")
      } else {
        return (this.$refs.contextMenu.style.top = this.entityContext.y + "px")
      }
    },
    calculateX() {
      if (this.entityContext.x >= this.parentWidth - this.childWidth) {
        return (this.$refs.contextMenu.style.left =
          this.entityContext.x - this.childWidth + "px")
      } else {
        return (this.$refs.contextMenu.style.left = this.entityContext.x + "px")
      }
    },
  },
}
</script>
