<template>
  <div
    v-if="actionItems.length > 0"
    ref="contextMenu"
    class="bg-white rounded absolute shadow-2xl py-1.5 px-1 z-20 space-y-1 border min-w-40"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }">
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      @click="
        () => {
          if (item.onClick) {
            item.onClick();
            close();
          }
        }
      ">
      <ColorPopover v-if="item.label === 'Color'" :entity-name="entityName" />
      <div v-else-if="item.label === 'Divider'" :entity-name="entityName">
        <hr />
      </div>
      <div
        v-else
        class="h-6 px-2 hover:bg-gray-100 text-sm cursor-pointer rounded-[5px] flex justify-start items-center">
        <FeatherIcon
          v-if="typeof item.icon === 'string'"
          :name="item.icon"
          class="h-3.5 mr-2"
          :class="[
            item.danger ? 'stroke-red-500 text-red-500' : '',
            item.label === 'Unfavourite' ? 'fill-amber-400 text-amber-400' : '',
          ]" />
        <component
          v-else
          class="w-3.5 mr-2 stroke-[1.5]"
          :class="[
            item.danger ? 'stroke-red-500 text-red-500' : '',
            item.label === 'Unfavourite' ? 'fill-amber-400 text-amber-400' : '',
          ]"
          :is="item.icon" />
        <div
          class="text-gray-800 mr-4"
          :class="[
            item.danger ? 'stroke-red-500 text-red-500' : '',
            item.label === 'Unfavourite' ? 'fill-amber-400 text-amber-400' : '',
          ]">
          {{ item.label }}
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from "frappe-ui";
import ColorPopover from "@/components/ColorPopover.vue";

export default {
  name: "EntityContextMenu",
  components: { FeatherIcon, ColorPopover },
  data() {
    return {
      parentWidth: null,
      parentHeight: null,
      childWidth: null,
      childHeight: null,
    };
  },
  mounted() {
    this.parentWidth = this.$refs.contextMenu.parentElement.clientWidth;
    this.parentHeight = this.$refs.contextMenu.parentElement.clientHeight;
    this.childWidth = this.$refs.contextMenu.clientWidth;
    this.childHeight = this.$refs.contextMenu.clientHeight;
    this.calculateY();
    this.calculateX();
    this.disableScroll();
  },
  updated() {
    this.calculateY();
    this.calculateX();
  },
  beforeUnmount() {
    this.enableScroll();
  },
  methods: {
    disableScroll() {
      document.querySelector("#currentPage").classList.add("disable-scroll");
    },
    enableScroll() {
      document.querySelector("#currentPage").classList.remove("disable-scroll");
    },
    calculateY() {
      if (this.entityContext.y >= this.parentHeight - this.childHeight) {
        return (this.$refs.contextMenu.style.top =
          this.entityContext.y - this.childHeight + "px");
      } else {
        return (this.$refs.contextMenu.style.top = this.entityContext.y + "px");
      }
    },
    calculateX() {
      if (this.entityContext.x >= this.parentWidth - this.childWidth) {
        return (this.$refs.contextMenu.style.left =
          this.entityContext.x - this.childWidth + "px");
      } else {
        return (this.$refs.contextMenu.style.left =
          this.entityContext.x + "px");
      }
    },
  },
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
};
</script>
<style>
.disable-scroll {
  overflow: hidden;
}
</style>
