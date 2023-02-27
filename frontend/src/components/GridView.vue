<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
    <div v-else class="h-full px-5 md:px-0" @click="deselectAll">
      <div class="mt-3" v-if="folders.length > 0">
        <div class="text-gray-600 font-medium">Folders</div>
        <div class="flex flex-row flex-wrap gap-5 mt-4">
          <div
            class="md:w-[212px] rounded-lg border group select-none"
            v-for="folder in folders"
            :key="folder.name"
            @dblclick="dblClickEntity(folder)"
            @click="selectEntity(folder, $event, displayOrderedEntities)"
            @contextmenu="
              handleEntityContext(folder, $event, displayOrderedEntities)
            "
            draggable="true"
            @dragstart="dragStart(folder, $event)"
            @drop="onDrop(folder)"
            @dragenter.prevent
            @dragover.prevent
            :class="
              selectedEntities.includes(folder)
                ? 'bg-blue-100'
                : 'hover:bg-blue-50'
            "
          >
            <div class="h-28 md:h-32 place-items-center grid">
              <svg
                :style="{ fill: folder.color }"
                :draggable="false"
                width="46"
                height="40"
                viewBox="0 0 46 40"
                fill="#32a852"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M0.368197 17.3301C0.17175 15.5535 1.56262 14.0004 3.35002 14.0004H42.65C44.4374 14.0004 45.8283 15.5535 45.6318 17.3301L43.7155 34.6599C43.3794 37.6999 40.8104 40.0004 37.7519 40.0004H8.24812C5.18961 40.0004 2.62062 37.6999 2.28447 34.6599L0.368197 17.3301Z"
                />
                <path
                  d="M43.125 11V9C43.125 6.79086 41.3341 5 39.125 5H20.312C20.1914 5 20.0749 4.95643 19.9839 4.8773L14.6572 0.245394C14.4752 0.0871501 14.2422 0 14.001 0H6.87501C4.66587 0 2.87501 1.79086 2.87501 4V11C2.87501 11.5523 3.32272 12 3.87501 12H42.125C42.6773 12 43.125 11.5523 43.125 11Z"
                />
              </svg>
            </div>
            <div class="px-3.5 pb-2.5">
              <h3 class="truncate text-[14px] font-medium">
                {{ folder.title }}
              </h3>
              <p class="truncate text-sm text-gray-600 mt-1">
                {{ folder.modified }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <div
        :class="folders.length > 0 ? 'mt-8' : 'mt-3'"
        v-if="files.length > 0"
      >
        <div class="text-gray-600 font-medium">Files</div>
        <div class="flex flex-row flex-wrap gap-5 mt-4">
          <div
            class="md:w-[212px] rounded-lg border group select-none"
            v-for="file in files"
            :key="file.name"
            @dblclick="dblClickEntity(file)"
            @click="selectEntity(file, $event, displayOrderedEntities)"
            draggable="true"
            @dragstart="dragStart(file, $event)"
            @dragenter.prevent
            @dragover.prevent
            :class="
              selectedEntities.includes(file)
                ? 'bg-blue-100'
                : 'hover:bg-blue-50'
            "
            @contextmenu="
              handleEntityContext(file, $event, displayOrderedEntities)
            "
          >
            <div class="h-28 md:h-32 place-items-center grid">
              <img
                :src="getIconUrl(formatMimeType(file.mime_type))"
                class="h-14"
                :draggable="false"
              />
            </div>
            <div class="px-3.5 md:h-16 content-center grid">
              <h3 class="truncate text-[14px] font-medium">{{ file.title }}</h3>
              <div
                class="truncate text-sm text-gray-600 flex mt-1 place-items-center"
              >
                <img
                  :src="getIconUrl(formatMimeType(file.mime_type))"
                  class="h-3.5 mr-1.5"
                />
                <p>{{ getFileSubtitle(file) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
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
    folders() {
      return this.folderContents
        ? this.folderContents.filter((x) => x.is_group === 1)
        : [];
    },
    files() {
      return this.folderContents
        ? this.folderContents.filter((x) => x.is_group === 0)
        : [];
    },
    displayOrderedEntities() {
      return this.folders.concat(this.files);
    },
  },
  emits: [
    'entitySelected',
    'openEntity',
    'showEntityContext',
    'showEmptyEntityContext',
    'fetchFolderContents',
  ],
  methods: {
    getFileSubtitle(file) {
      let fileSubtitle = formatMimeType(file.mime_type);
      fileSubtitle =
        fileSubtitle.charAt(0).toUpperCase() + fileSubtitle.slice(1);
      return `${fileSubtitle} ∙ ${file.modified}`;
    },
    selectEntity(entity, event, entities) {
      event.stopPropagation();
      this.$emit('showEntityContext', null);
      this.$emit('showEmptyEntityContext', null);
      let selectedEntities = this.selectedEntities;
      if (event.ctrlKey || event.metaKey) {
        const index = selectedEntities.indexOf(entity);
        index > -1
          ? selectedEntities.splice(index, 1)
          : selectedEntities.push(entity);
        this.$emit('entitySelected', selectedEntities);
      } else if (event.shiftKey) {
        let shiftSelect;
        selectedEntities.push(entity);
        const firstIndex = entities.indexOf(selectedEntities[0]);
        const lastIndex = entities.indexOf(
          selectedEntities[selectedEntities.length - 1]
        );
        if (firstIndex > lastIndex) {
          shiftSelect = entities.slice(lastIndex, firstIndex);
        } else {
          shiftSelect = entities.slice(firstIndex, lastIndex);
        }
        shiftSelect.slice(1).map((file) => {
          selectedEntities.push(file);
        });
      } else {
        selectedEntities = [entity];
        this.$emit('entitySelected', selectedEntities);
      }
      this.$store.commit(
        'setEntityInfo',
        selectedEntities[selectedEntities.length - 1]
      );
    },
    dblClickEntity(entity) {
      this.$emit('openEntity', entity);
    },
    deselectAll() {
      this.$emit('entitySelected', []);
      this.$store.commit('setEntityInfo', null);
      this.$emit('showEntityContext', null);
    },
    handleEntityContext(entity, event, entities) {
      event.preventDefault(event);
      if (this.selectedEntities.length <= 1) {
        this.selectEntity(entity, event, entities);
      }
      this.$store.commit('setEntityInfo', entity);
      this.$emit('showEntityContext', { x: event.clientX, y: event.clientY });
    },
    dragStart(entity, event) {
      event.dataTransfer.dropEffect = 'move';
      event.dataTransfer.effectAllowed = 'move';
      // for when a user directly drags a single file 
      if (this.selectedEntities.length <= 1) {
        this.selectEntity(entity, event) 
      }
    },

    async onDrop(newParent) {
      for (let i = 0; i < this.selectedEntities.length; i++) {
        await this.$resources.moveEntity.submit({
          method: 'move',
          entity_name: this.selectedEntities[i].name,
          new_parent: newParent.name,
        });
      }
      this.deselectAll();
      this.$emit('fetchFolderContents');
    },
  },
  resources: {
    moveEntity() {
      return {
        url: 'drive.api.files.call_controller_method',
        method: 'POST',
        params: {
          method: 'move',
          entity_name: 'entity name',
          new_parent: 'new entity parent',
        },
        validate(params) {
          if (!params?.new_parent) {
            return 'New parent is required';
          }
        },
      };
    },
  },
  setup() {
    return { formatMimeType, getIconUrl };
  },
};
</script>
