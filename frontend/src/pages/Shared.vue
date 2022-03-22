<template>
  <div class="h-full">
    <div
      v-if="$resources.folderContents.error"
      class="relative h-full p-5 flex flex-col lg:flex-row justify-center items-center text-center bg-neutral-50 rounded-lg"
    >
      <div class="w-8 h-8 p-1.5 m-4 rounded-full bg-red-100">
        <FeatherIcon name="x" class="text-red-500" />
      </div>
      <p class="text-2xl font-semibold">
        {{ $resources.folderContents.error.messages.join('\n') }}
      </p>
      <Button
        class="absolute left-0 top-0 m-4 focus:ring-0 focus:ring-offset-0 bg-gray-200 hover:bg-gray-300"
        @click="$router.go(-1)"
        icon="chevron-left"
      />
    </div>
    <ListView
      :folderContents="$resources.folderContents.data"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
    >
      <DriveToolBar
        :actionItems="actionItems"
        :breadcrumbs="breadcrumbs"
        :showUploadButton="false"
      />
    </ListView>
    <FilePreview
      v-if="showPreview"
      @hide="hidePreview"
      :previewEntity="previewEntity"
    />
  </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import ListView from '@/components/ListView.vue'
import DriveToolBar from '@/components/DriveToolBar.vue'
import FilePreview from '@/components/FilePreview.vue'

export default {
  name: 'Shared',
  components: {
    FeatherIcon,
    ListView,
    DriveToolBar,
    FilePreview,
  },
  data: () => ({
    previewEntity: null,
    showPreview: false,
    selectedEntities: [],
    breadcrumbs: [{ label: 'Shared files', route: '/shared' }],
  }),
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    actionItems() {
      return [
        {
          label: 'Download',
          action: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              !this.selectedEntities[0].is_group
            )
          },
        },
      ].filter((item) => item.isEnabled())
    },
  },
  methods: {
    openEntity(entity) {
      this.previewEntity = entity
      this.showPreview = true
    },
    hidePreview() {
      this.showPreview = false
      this.previewEntity = null
    },
    formatSize(size, nDigits = 1) {
      if (size === 0) return '0 B'
      const k = 1024
      const digits = nDigits < 0 ? 0 : nDigits
      const sizes = [' B', ' KB', ' MB', ' GB', ' TB', ' PB']
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
        method: 'drive.api.permissions.get_shared_with_me',
        cache: ['folderContents', this.userId],
        onSuccess(data) {
          this.$resources.folderContents.error = null
          data.forEach((entity, index) => {
            if (entity.is_group) {
              data.splice(index, 1)
            } else {
              entity.size_in_bytes = entity.file_size
              entity.file_size = entity.is_group
                ? '-'
                : this.formatSize(entity.file_size)
              entity.modified = this.formatDate(entity.modified)
              entity.creation = this.formatDate(entity.creation)
              entity.owner = entity.owner === this.userId ? 'me' : entity.owner
            }
          })
        },
        auto: true,
      }
    },
  },
}
</script>
