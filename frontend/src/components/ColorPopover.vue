<template>
  <Popover
    trigger="hover"
    placement="right-start"
    :hoverDelay="0.5"
    :leaveDelay="0.5"
    class="hover:bg-gray-100 rounded-lg flex px-3"
  >
    <template #target>
      <div class="h-7 flex items-center">
        <FeatherIcon
          name="droplet"
          class="stroke-1.5 w-4 h-4 text-gray-700 mr-3"
        />
        <div class="text-gray-800">Change Color</div>
        <FeatherIcon
          :name="'chevron-right'"
          class="w-4 h-4 text-gray-700 ml-16"
        />
      </div>
    </template>
    <template #body-main>
      <div class="grid grid-cols-5 gap-2 p-3">
        <button
          v-for="color in colors"
          class="h-6 w-6 rounded-md justify-self-center"
          :style="{ backgroundColor: color }"
          :value="entity?.color"
          @click="
            $resources.updateColor.submit({
              method: 'change_color',
              entity_name: this.entityName,
              new_color: color,
            })
          "
        />
      </div>
    </template>
  </Popover>
</template>

<script>
import { Popover, Button, FeatherIcon } from 'frappe-ui';
import { theme } from '@/utils/theme';

export default {
  name: 'ColorPopover',
  components: { Popover, Button, FeatherIcon },
  emits: ['success'],
  data() {
    return {
      colors: [
        'slate',
        'gray',
        'zinc',
        'neutral',
        'stone',
        'red',
        'orange',
        'amber',
        'yellow',
        'lime',
        'green',
        'emerald',
        'teal',
        'cyan',
        'sky',
        'blue',
        'indigo',
        'violet',
        'purple',
        'fuchsia',
      ].map((color) => theme.colors[color]['500']),
    };
  },
  props: {
    entityName: {
      type: String,
    },
  },
  resources: {
    updateColor() {
      return {
        url: 'drive.api.files.call_controller_method',
        params: {
          method: 'change_color',
          entity_name: this.entityName,
        },
        validate(params) {
          if (!params?.new_color) {
            return 'New name is required';
          }
        },
        onSuccess() {
          this.emitter.emit('fetchFolderContents');
        },
      };
    },
  },
};
</script>
