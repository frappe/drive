<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <table class="max-h-full min-w-full">
      <thead class="sticky top-0 bg-white shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-100">
        <tr v-if="!isEmpty" class="text-left text-base text-gray-600">
          <th class="w-6 px-5">
            <Input type="checkbox" class="invisible" />
          </th>
          <th class="hidden px-2.5 py-3.5 font-normal md:table-cell">
            Name
          </th>
          <th class="hidden px-2.5 py-3.5 font-normal lg:table-cell">Owner</th>
          <th class="hidden px-2.5 py-3.5 font-normal md:table-cell">
            Modified
          </th>
          <th class="hidden px-2.5 py-3.5 font-normal lg:table-cell">Size</th>
        </tr>
      </thead>
      <tbody v-if="!isEmpty" class="divide-y divide-gray-100">
        <tr v-for="entity in filteredContents" :key="entity.name"
          class="group select-none text-base text-gray-500 hover:bg-gray-50">
          <td class="w-6 px-5" @click="selectEntity(entity)">
            <Input type="checkbox" :checked="selectedEntities.includes(entity)" class="focus:ring-0 focus:ring-offset-0"
              :class="
                selectedEntities.includes(entity) ? 'visible' : 'group-hover:visible md:invisible'
              " />
          </td>
          <td @click="this.$emit('openEntity', entity)" class="min-w-[15rem] px-2.5 py-3.5 lg:w-2/5">
            <div class="flex items-center text-gray-900 text-[14px] font-medium">
              <img :src="getIconUrl(entity.is_group ? 'folder'
              : formatMimeType(entity.mime_type))" class="h-5 mr-5" />
              {{ entity.title }}
            </div>
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="hidden w-36 truncate px-2.5 py-3.5 font-normal lg:table-cell lg:w-1/5 text-gray-700">
            {{ entity.owner }}
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="hidden w-36 truncate px-2.5 py-3.5 font-normal md:table-cell lg:w-1/5 text-gray-700">
            {{ entity.modified }}
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="hidden w-36 truncate px-2.5 py-3.5 font-normal lg:table-cell lg:w-1/5 text-gray-700">
            {{ entity.file_size }}
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="isEmpty" class="flex-1">
      <slot name="placeholder"></slot>
    </div>
  </div>
</template>
<script>
import { Input, FeatherIcon } from 'frappe-ui'
import { formatMimeType } from '@/utils/format'
import getIconUrl from '@/utils/getIconUrl'

export default {
  name: 'ListView',
  components: {
    Input,
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
  emits: ['entitySelected', 'openEntity'],
  computed: {
    filteredContents() {
      return this.folderContents ? this.folderContents : []
    },
    isEmpty() {
      return this.filteredContents && this.filteredContents.length === 0
    },
  },
  methods: {
    selectEntity(entity) {
      let selectedEntities = this.selectedEntities
      const index = selectedEntities.indexOf(entity)
      index > -1 ? selectedEntities.splice(index, 1) : selectedEntities.push(entity)
      this.$emit('entitySelected', selectedEntities)
      this.$store.commit('setEntityInfo', selectedEntities[selectedEntities.length - 1])
    },
  },
  setup() {
    return { formatMimeType, getIconUrl }
  }
}
</script>
