<template>
  <div
    class="bg-white rounded-xl absolute shadow-md p-2 z-10 space-y-0.5 border"
    :style="{ left: `${entityContext.x}px`, top: `${entityContext.y}px` }"
    v-if="actionItems.length > 0">
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      class="text-sm h-7 hover:bg-gray-100 cursor-pointer rounded-lg flex px-3 items-center"
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
  props: {
    actionItems: {
      type: Array,
    },
    entityContext: {
      type: Object,
    },
    close: {
      type: Function,
    },
  },
};
</script>
