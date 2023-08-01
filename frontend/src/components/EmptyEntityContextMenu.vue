<template>
  <div
    v-if="actionItems.length > 0"
    ref="emptyContextMenu"
    class="bg-white rounded-md absolute shadow-sm p-2 z-20 space-y-0.5 border"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }">
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      class="text-sm h-7 hover:bg-gray-100 cursor-pointer rounded-md flex px-3 items-center"
      @click="
        () => {
          item.handler();
          close();
        }
      ">
      <FeatherIcon
        :name="item.icon"
        class="stroke-1.5 w-4 h-4 text-gray-700 mr-3" />
      <div class="text-gray-800 text-small">{{ item.label }}</div>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from "frappe-ui";

export default {
  name: "EmptyEntityContext",
  components: { FeatherIcon },
  data() {
    return {
      parentWidth: null,
      parentHeight: null,
      childWidth: null,
      childHeight: null,
    };
  },
  mounted() {
    this.parentWidth = this.$refs.emptyContextMenu.parentElement.clientWidth;
    this.parentHeight = this.$refs.emptyContextMenu.parentElement.clientHeight;
    this.childWidth = this.$refs.emptyContextMenu.clientWidth;
    this.childHeight = this.$refs.emptyContextMenu.clientHeight;
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
        return (this.$refs.emptyContextMenu.style.top =
          this.entityContext.y - this.childHeight + "px");
      } else {
        return (this.$refs.emptyContextMenu.style.top =
          this.entityContext.y + "px");
      }
    },
    calculateX() {
      if (this.entityContext.x >= this.parentWidth - this.childWidth) {
        return (this.$refs.emptyContextMenu.style.left =
          this.entityContext.x - this.childWidth + "px");
      } else {
        return (this.$refs.emptyContextMenu.style.left =
          this.entityContext.x + "px");
      }
    },
  },
  props: {
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
