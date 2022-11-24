<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
    <div v-else class="h-full px-5 md:px-0" @click="deselectAll">
      <table class="max-h-full min-w-full">
        <thead
          class="sticky top-0 bg-white shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-200"
        >
          <tr class="text-left text-base text-gray-600">
            <th class="hidden px-2.5 py-3 font-normal md:table-cell">Name</th>
            <th class="hidden px-2.5 py-3 font-normal lg:table-cell">Owner</th>
            <th class="hidden px-2.5 py-3 font-normal md:table-cell">
              Modified
            </th>
            <th class="hidden px-2.5 py-3 font-normal lg:table-cell">Size</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entity in folderContents"
            :key="entity.name"
            class="group select-none text-base shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-200"
            :class="
              selectedEntities.includes(entity)
                ? 'bg-gray-100'
                : 'hover:bg-gray-50'
            "
            @click="selectEntity(entity, $event)"
            @contextmenu="handleEntityContext(entity, $event)"
          >
            <td class="min-w-[15rem] px-2.5 py-3 lg:w-3/6">
              <div
                class="flex items-center text-gray-900 text-[14px] font-medium truncate"
              >
                <img
                  :src="
                    getIconUrl(
                      entity.is_group
                        ? 'folder'
                        : formatMimeType(entity.mime_type)
                    )
                  "
                  class="h-[21px] mr-5"
                />
                {{ entity.title }}
              </div>
            </td>
            <td
              class="hidden w-36 truncate px-2.5 py-3 font-normal lg:table-cell lg:w-1/6 text-gray-700"
            >
              {{ entity.owner }}
            </td>
            <td
              class="hidden w-36 truncate px-2.5 py-3 font-normal md:table-cell lg:w-1/6 text-gray-700"
            >
              {{ entity.modified }}
            </td>
            <td
              class="hidden w-36 truncate px-2.5 py-3 font-normal lg:table-cell lg:w-1/6 text-gray-700"
            >
              {{ entity.file_size }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from 'frappe-ui';
import { formatMimeType } from '@/utils/format';
import getIconUrl from '@/utils/getIconUrl';

export default {
  name: 'GridView',
  components: {
    FeatherIcon,
  },
  props: {
    folderContents: {
      type: Array,
    },
    selectedEntities: {
      type: Array,
    },
  },
  computed: {
    isEmpty() {
      return this.folderContents && this.folderContents.length === 0;
    },
  },
  emits: ['entitySelected', 'openEntity', 'showEntityContext'],
  methods: {
    getFileSubtitle(file) {
      let fileSubtitle = formatMimeType(file.mime_type);
      fileSubtitle =
        fileSubtitle.charAt(0).toUpperCase() + fileSubtitle.slice(1);
      return `${fileSubtitle} ∙ ${file.modified}`;
    },
    selectEntity(entity, event) {
      event.stopPropagation();
      this.$emit('showEntityContext', null);
      let selectedEntities = this.selectedEntities;
      if (event.ctrlKey || event.metaKey) {
        const index = selectedEntities.indexOf(entity);
        index > -1
          ? selectedEntities.splice(index, 1)
          : selectedEntities.push(entity);
        this.$emit('entitySelected', selectedEntities);
      } else {
        if (selectedEntities.length === 1 && selectedEntities[0] === entity) {
          this.$emit('openEntity', entity);
          if (entity.is_group === 1) this.deselectAll();
        } else {
          selectedEntities = [entity];
          this.$emit('entitySelected', selectedEntities);
        }
      }
      this.$store.commit(
        'setEntityInfo',
        selectedEntities[selectedEntities.length - 1]
      );
    },
    deselectAll() {
      this.$emit('entitySelected', []);
      this.$store.commit('setEntityInfo', null);
      this.$emit('showEntityContext', null);
    },
    handleEntityContext(entity, event) {
      this.$emit('entitySelected', [entity]);
      this.$store.commit('setEntityInfo', entity);
      this.$emit('showEntityContext', { x: event.clientX, y: event.clientY });
      event.preventDefault();
    },
  },
  setup() {
    return { formatMimeType, getIconUrl };
  },
};
</script>
