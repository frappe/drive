<template>
  <div
    class="bg-white rounded-xl absolute shadow-md p-2 z-10 space-y-0.5 border"
    :style="{ left: `${entityContext.x}px`, top: `${entityContext.y}px` }"
    v-if="actionItems.length > 0"
  >
    <div
      v-for="(item, index) in actionItems"
      :key="index"
      class="text-sm"
      @click="
        () => {
          item.handler();
          close();
        }
      "
    >
      <Popover
        v-if="item.label === 'Change Color'"
        trigger="hover"
        placement="right-start"
        :hoverDelay="0.5"
        :leaveDelay="0.5"
        class="hover:bg-gray-100 cursor-pointer rounded-lg flex px-3"
      >
        <template #target>
          <div class="h-7 flex items-center">
            <FeatherIcon
              :name="item.icon"
              class="stroke-1.5 w-4 h-4 text-gray-700 mr-3"
            />
            <div class="text-gray-800">{{ item.label }}</div>
            <FeatherIcon
              :name="'chevron-right'"
              class="w-4 h-4 text-gray-700 ml-20"
            />
          </div>
        </template>
        <template #body-main>
          <div class="p-2 text-base">Popup content</div>
        </template>
      </Popover>
      <div
        v-else
        class="h-7 hover:bg-gray-100 cursor-pointer rounded-lg flex px-3 items-center"
      >
        <FeatherIcon
          :name="item.icon"
          class="stroke-1.5 w-4 h-4 text-gray-700 mr-3"
        />
        <div class="text-gray-800">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>
<script>
import { FeatherIcon, Popover, Button } from 'frappe-ui';

export default {
  name: 'EntityContextMenu',
  components: { FeatherIcon, Popover, Button },
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
