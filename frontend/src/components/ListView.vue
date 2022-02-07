<template>
  <table class="min-w-full max-h-full divide-y divide-gray-100">
    <thead>
      <tr class="text-base text-left text-gray-500">
        <th class="hidden sm:table-cell w-2/5 pl-20 pr-5 py-3.5 font-normal">
          Name
        </th>
        <th class="hidden sm:table-cell w-1/5 px-5 py-3.5 font-normal">
          Owner
        </th>
        <th class="hidden md:table-cell w-1/5 px-5 py-3.5 font-normal">
          Modified
        </th>
        <th class="hidden lg:table-cell w-1/5 px-5 py-3.5 font-normal">Size</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      <tr
        v-for="entity in $resources.folderContents.data"
        :key="entity.name"
        class="text-base text-gray-500 hover:bg-gray-50 group"
        @click="selectEntity(entity)"
      >
        <td class="w-2/5 px-5 py-3.5 font-normal text-zinc-800">
          <div class="flex items-center">
            <div class="w-6">
              <Input
                type="checkbox"
                :checked="entity.selected"
                :class="entity.selected ? 'block' : 'hidden group-hover:block'"
              />
            </div>
            <div class="p-2.5">
              <FeatherIcon
                :name="entity.is_group ? 'folder' : 'file'"
                class="w-3.5 h-3.5 stroke-2 stroke-gray-400"
              />
            </div>
            {{ entity.title }}
          </div>
        </td>
        <td class="hidden sm:table-cell w-1/5 px-5 py-3.5 font-normal truncate">
          {{ entity.owner }}
        </td>
        <td class="hidden md:table-cell w-1/5 px-5 py-3.5 font-normal truncate">
          {{ entity.modified }}
        </td>
        <td class="hidden lg:table-cell w-1/5 px-5 py-3.5 font-normal truncate">
          {{ entity.file_size }}
        </td>
      </tr>
    </tbody>
  </table>
</template>
<script>
import { FeatherIcon, Input } from 'frappe-ui'

export default {
  name: 'ListView',
  components: {
    FeatherIcon,
    Input,
  },
  props: {
    entityName: {
      type: String,
      required: false,
    },
  },
  emits: ['entitySelected'],
  methods: {
    selectEntity(entity) {
      entity.selected = !entity.selected
      let selectedEntities = this.$resources.folderContents.data.filter(
        (entity) => entity.selected
      )
      this.$emit('entitySelected', selectedEntities)
    },
    formatSize(size, nDigits = 1) {
      if (size === 0) return '0 B'
      const k = 1024
      const digits = nDigits < 0 ? 0 : nDigits
      const sizes = ['B ', 'KB ', 'MB ', 'GB ', 'TB ', 'PB ']
      const i = Math.floor(Math.log(size) / Math.log(k))
      return parseFloat((size / Math.pow(k, i)).toFixed(digits)) + sizes[i]
    },
    getDateDiffInDays(date1, date2) {
      const msPerDay = 1000 * 60 * 60 * 24
      const date1UTC = Date.UTC(
        date1.getFullYear(),
        date1.getMonth(),
        date1.getDate()
      )
      const date2UTC = Date.UTC(
        date2.getFullYear(),
        date2.getMonth(),
        date2.getDate()
      )
      return Math.floor((date1UTC - date2UTC) / msPerDay)
    },
    formatDate(date) {
      date = new Date(date)
      let todaysDate = new Date()
      let prefix = ''
      let options = {}
      if (this.getDateDiffInDays(todaysDate, date) < 1) {
        prefix = 'Today, '
        options = { hour: 'numeric', minute: 'numeric' }
      } else if (this.getDateDiffInDays(date, todaysDate) == 1) {
        prefix = 'Yesterday, '
        options = { hour: 'numeric', minute: 'numeric' }
      } else if (this.getDateDiffInDays(date, todaysDate) < 364) {
        options = { month: 'long', day: 'numeric' }
      } else {
        options = { year: 'numeric', month: 'long', day: 'numeric' }
      }
      return prefix + date.toLocaleString(undefined, options)
    },
  },
  resources: {
    folderContents() {
      return {
        method: 'drive.api.files.list_folder_contents',
        cache: ['folderContents', this.entityName],
        params: {
          name: this.entityName,
        },
        onSuccess(data) {
          data.forEach((entity) => {
            entity.file_size = entity.is_group
              ? '-'
              : this.formatSize(entity.file_size)
            entity.modified = this.formatDate(entity.modified)
          })
        },
        auto: true,
      }
    },
  },
}
</script>
