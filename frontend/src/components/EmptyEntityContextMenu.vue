<template>
  <div
    v-if="actionItems.length > 0"
    ref="emptyContextMenu"
    class="bg-white rounded absolute shadow-2xl py-1.5 px-1 z-20 space-y-1 border min-w-40"
    :style="{ left: `${calculateX}px`, top: `${calculateY}px` }">
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      @click="
        () => {
          item.handler();
          close();
        }
      ">
      <div v-if="item.label === 'Divider'">
        <hr />
      </div>
      <div
        v-else
        class="h-6 px-2 hover:bg-gray-100 text-sm whitespace-nowrap cursor-pointer rounded-[5px] flex justify-start items-center">
        <FeatherIcon :name="item.icon" class="h-3.5 text-gray-800 mr-2" />
        <div class="text-gray-800 mr-4">{{ item.label }}</div>
      </div>
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
