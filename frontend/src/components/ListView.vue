<template>
  <div>
    <div class="sticky top-0 bg-white pt-2 sm:pt-0">
      <DriveToolBar :breadcrumbs="breadcrumbs" :actionItems="actionItems" />
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
          v-for="entity in $resources.folderContents.data"
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
    actionItems: {
      type: Array,
      required: true,
    },
  },
  emits: ['entitySelected', 'openEntity'],
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    breadcrumbs() {
      if (!this.entityName || this.$resources.pathEntities.data === null) {
        return [
          {
            label: 'Home',
            route: { name: 'Home', params: { entityName: '' } },
          },
        ]
      }
      let breadcrumbs = []
      this.$resources.pathEntities.data.forEach((entity, index) => {
        if (index === 0) {
          breadcrumbs.push({
            label: entity.owner === this.userId ? 'Home' : entity.title,
            route: { name: 'Home', params: { entityName: '' } },
          })
        } else {
          breadcrumbs.push({
            label: entity.title,
            route: `/folder/${entity.name}`,
          })
        }
      })
      if (breadcrumbs.length > 4) {
        breadcrumbs.splice(1, breadcrumbs.length - 4, {
          label: '...',
          route: '',
        })
      }
      return breadcrumbs
    },
  },
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
          entity_name: this.entityName,
        },
        onSuccess(data) {
          data.forEach((entity) => {
            entity.file_size = entity.is_group
              ? '-'
              : this.formatSize(entity.file_size)
            entity.modified = this.formatDate(entity.modified)
            entity.owner = entity.owner === this.userId ? 'me' : entity.owner
          })
        },
        auto: true,
      }
    },
    pathEntities() {
      return {
        method: 'drive.api.files.get_entities_in_path',
        cache: ['pathEntities', this.entityName],
        params: {
          entity_name: this.entityName,
        },
        auto: Boolean(this.entityName),
      }
    },
  },
}
</script>
