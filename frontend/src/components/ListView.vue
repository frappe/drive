<template>
  <div>
    <div class="sticky top-0 bg-white pt-2 sm:pt-0">
      <DriveToolBar @uploadFile="$emit('uploadFile')" />
      <table class="min-w-full max-h-full divide-y divide-gray-100">
        <thead class="shadow-[0_1px_0_0_rgba(0,0,0,0.1)] shadow-gray-100">
          <tr class="text-base text-left text-gray-500">
            <th
              class="hidden sm:table-cell w-2/5 pl-20 pr-5 py-3.5 font-normal"
            >
              Name
            </th>
            <th class="hidden sm:table-cell w-1/5 px-5 py-3.5 font-normal">
              Owner
            </th>
            <th class="hidden md:table-cell w-1/5 px-5 py-3.5 font-normal">
              Modified
            </th>
            <th class="hidden lg:table-cell w-1/5 px-5 py-3.5 font-normal">
              Size
            </th>
          </tr>
        </thead>
      </table>
    </div>
    <table class="min-w-full max-h-full divide-y divide-gray-100">
      <tbody class="divide-y divide-gray-100">
        <tr
          v-for="entity in folderContents"
          :key="entity.name"
          class="text-base text-gray-500 select-none hover:bg-gray-50 group"
          @click="this.$emit('openEntity', entity)"
        >
          <td class="w-2/5 px-5 py-3.5 font-normal text-zinc-800">
            <div class="flex items-center">
              <div class="w-6">
                <Input
                  type="checkbox"
                  :checked="entity.selected"
                  class="focus:ring-0 focus:ring-offset-0"
                  :class="
                    entity.selected ? 'block' : 'hidden group-hover:block'
                  "
                  @click.stop="selectEntity(entity)"
                />
              </div>
              <div class="px-2.5">
                <FeatherIcon
                  :name="entity.is_group ? 'folder' : 'file'"
                  class="w-3.5 h-3.5 stroke-2 stroke-gray-400"
                />
              </div>
              {{ entity.title }}
            </div>
          </td>
          <td
            class="hidden sm:table-cell w-1/5 px-5 py-3.5 font-normal truncate"
          >
            {{ entity.owner }}
          </td>
          <td
            class="hidden md:table-cell w-1/5 px-5 py-3.5 font-normal truncate"
          >
            {{ entity.modified }}
          </td>
          <td
            class="hidden lg:table-cell w-1/5 px-5 py-3.5 font-normal truncate"
          >
            {{ entity.file_size }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script>
import { FeatherIcon, Input } from 'frappe-ui'
import DriveToolBar from '@/components/DriveToolBar.vue'

export default {
  name: 'ListView',
  components: {
    FeatherIcon,
    Input,
    DriveToolBar,
  },
  props: {
    entityName: {
      type: String,
      required: true,
    },
    folderContents: {
      type: Array,
      required: true,
    },
  },
  emits: ['entitySelected', 'openEntity', 'uploadFile'],
  methods: {
    selectEntity(entity) {
      entity.selected = !entity.selected
      let selectedEntities = this.folderContents.filter(
        (entity) => entity.selected
      )
      this.$emit('entitySelected', selectedEntities)
    },
  },
}
</script>
