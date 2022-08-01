<template>
  <div class="h-full flex flex-col">
    <slot name="toolbar"></slot>
    <table class="max-h-full min-w-full">
      <thead class="sticky top-0 bg-white shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-100">
        <tr v-if="!isEmpty" class="text-left text-base text-gray-500">
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
        <tr v-for="entity in folderContents" :key="entity.name"
          class="group select-none text-base text-gray-500 hover:bg-gray-50">
          <td class="w-6 px-5" @click="selectEntity(entity)">
            <Input type="checkbox" :checked="entity.selected" class="focus:ring-0 focus:ring-offset-0" :class="
              entity.selected ? 'visible' : 'group-hover:visible md:invisible'
            " />
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="min-w-[15rem] px-2.5 py-3.5 font-normal text-zinc-800 lg:w-2/5">
            <div class="flex items-center">
              <FeatherIcon :name="entity.is_group ? 'folder' : 'file'"
                class="mr-2.5 h-3.5 w-3.5 stroke-gray-400 stroke-2" />
              {{ entity.title }}
            </div>
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="hidden w-36 truncate px-2.5 py-3.5 font-normal lg:table-cell lg:w-1/5">
            {{ entity.owner }}
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="hidden w-36 truncate px-2.5 py-3.5 font-normal md:table-cell lg:w-1/5">
            {{ entity.modified }}
          </td>
          <td @click="this.$emit('openEntity', entity)"
            class="hidden w-36 truncate px-2.5 py-3.5 font-normal lg:table-cell lg:w-1/5">
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
  },
  emits: ['entitySelected', 'openEntity'],
  computed: {
    isEmpty() {
      return this.folderContents && this.folderContents.length === 0
    },
  },
  methods: {
    selectEntity(entity) {
      entity.selected = !entity.selected
      const selectedEntities = this.folderContents.filter(
        (entity) => entity.selected
      )
      this.$emit('entitySelected', selectedEntities)
    },
  },
}
</script>
