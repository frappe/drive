<template>
  <div
    v-if="actionItems.length > 0"
    ref="contextMenu"
    class="bg-white rounded-md absolute shadow-2xl p-1.5 z-20 space-y-0.5 border"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }">
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      class="text-sm"
      @click="
        () => {
          if (item.onClick) {
            item.onClick();
            close();
          }
        }
      ">
      <ColorPopover
        v-if="item.label === 'Change Color'"
        :entity-name="entityName" />
      <div
        v-else
        class="h-7 hover:bg-gray-100 cursor-pointer rounded flex px-3 items-center">
        <FeatherIcon
          :name="item.icon"
          class="stroke-1.5 w-4 h-4 text-gray-700 mr-3" />
        <div class="text-gray-800">{{ item.label }}</div>
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
  },
  updated() {
    this.calculateY();
    this.calculateX();
  },
  methods: {
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
