<template>
  <div class="h-full">
    <FolderContentsError
      v-if="$resources.folderContents.error"
      :error="$resources.folderContents.error"
    />
    <ListView
      v-else
      :folderContents="$resources.folderContents.data"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
    >
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :showUploadButton="false"
        />
      </template>
      <template #placeholder>
        <NoFilesSection secondaryMessage="No files have been shared with you" />
      </template>
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
import NoFilesSection from '@/components/NoFilesSection.vue'
import FilePreview from '@/components/FilePreview.vue'
import FolderContentsError from '@/components/FolderContentsError.vue'
import { formatSize, formatDate } from '@/utils/format'

export default {
  name: 'Shared',
  components: {
    FeatherIcon,
    ListView,
    DriveToolBar,
    NoFilesSection,
    FilePreview,
    FolderContentsError,
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
  },
  resources: {
    folderContents() {
      return {
        method: 'drive.api.permissions.get_shared_with_me',
        cache: ['folderContents', this.userId],
        onSuccess(data) {
          this.$resources.folderContents.error = null
          data = data.filter((entity) => !entity.is_group)
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size
            entity.file_size = entity.is_group
              ? '-'
              : formatSize(entity.file_size)
            entity.modified = formatDate(entity.modified)
            entity.creation = formatDate(entity.creation)
            entity.owner = entity.owner === this.userId ? 'me' : entity.owner
          })
          this.$resources.folderContents.data = data
        },
        auto: true,
      }
    },
  },
}
</script>
