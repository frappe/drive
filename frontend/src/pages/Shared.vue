<template>
  <div class="h-full flex flex-col">
    <FolderContentsError v-if="$resources.folderContents.error" :error="$resources.folderContents.error" />

    <GridView v-else-if="$store.state.view === 'grid'" :folderContents="$resources.folderContents.data"
      @entitySelected="(selected) => (selectedEntities = selected)" :selectedEntities="selectedEntities"
      @openEntity="(entity) => openEntity(entity)">
      <template #toolbar>
        <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :showUploadButton="false" />
      </template>
      <template #placeholder>
        <NoFilesSection secondaryMessage="No files have been shared with you" />
      </template>
    </GridView>

    <ListView v-else :folderContents="$resources.folderContents.data"
      @entitySelected="(selected) => (selectedEntities = selected)" :selectedEntities="selectedEntities"
      @openEntity="(entity) => openEntity(entity)">
      <template #toolbar>
        <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :showUploadButton="false" />
      </template>
      <template #placeholder>
        <NoFilesSection secondaryMessage="No files have been shared with you" />
      </template>
    </ListView>

    <FilePreview v-if="showPreview" @hide="hidePreview" :previewEntity="previewEntity" />
    <RenameDialog v-model="showRenameDialog" :entity="selectedEntities[0]" @success="
      () => {
        $resources.folderContents.fetch()
        showRenameDialog = false
        selectedEntities = []
      }
    " />
    <GeneralDialog v-model="showRemoveDialog" :entities="selectedEntities" :for="'unshare'" @success="
      () => {
        $resources.folderContents.fetch()
        showRemoveDialog = false
        selectedEntities = []
      }
    " />
  </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import ListView from '@/components/ListView.vue'
import GridView from '@/components/GridView.vue'
import DriveToolBar from '@/components/DriveToolBar.vue'
import NoFilesSection from '@/components/NoFilesSection.vue'
import FilePreview from '@/components/FilePreview.vue'
import FolderContentsError from '@/components/FolderContentsError.vue'
import RenameDialog from '@/components/RenameDialog.vue'
import GeneralDialog from '@/components/GeneralDialog.vue'
import { formatSize, formatDate } from '@/utils/format'

export default {
  name: 'Shared',
  components: {
    FeatherIcon,
    ListView,
    GridView,
    DriveToolBar,
    RenameDialog,
    GeneralDialog,
    NoFilesSection,
    FilePreview,
    FolderContentsError,
  },
  data: () => ({
    previewEntity: null,
    showPreview: false,
    showRenameDialog: false,
    showRemoveDialog: false,
    userAccess: {},
    selectedEntities: [],
    breadcrumbs: [{ label: 'Shared With Me', route: '/shared' }],
  }),
  props: {
    entityName: {
      type: String,
      required: false,
      default: '',
    },
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    actionItems() {
      return [
        {
          label: 'Download',
          handler: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 && !this.selectedEntities[0].is_group
            )
          },
        },
        {
          label: 'Rename',
          handler: () => {
            this.showRenameDialog = true
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 && this.selectedEntities[0].write
            )
          },
        },
        {
          label: 'Remove',
          handler: () => {
            this.showRemoveDialog = true
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 && this.selectedEntities.every(x => !x.everyone)
            )
          },
        },
      ].filter((item) => item.isEnabled())
    },
  },
  methods: {
    openEntity(entity) {
      if (entity.is_group) {
        this.selectedEntities = []
        this.$router.push({
          name: 'SharedFolder',
          params: { entityName: entity.name },
        })
      } else {
        this.previewEntity = entity
        this.showPreview = true
      }
    },
    hidePreview() {
      this.showPreview = false
      this.previewEntity = null
    },
  },
  watch: {
    entityName(newEntityName) {
      if (!newEntityName) {
        this.breadcrumbs = [{ label: 'Shared With Me', route: '/shared' }]
      }
    },
  },
  resources: {
    folderAccess() {
      return {
        method: 'drive.api.permissions.get_user_access',
        params: { entity_name: this.entityName, },
        onSuccess(data) {
          this.userAccess = data
        },
      }
    },

    folderContents() {
      return {
        method: 'drive.api.permissions.get_shared_with_me',
        cache: ['folderContents', this.userId, this.entityName],
        params: { entity_name: this.entityName },
        onSuccess(data) {
          this.$resources.folderContents.error = null
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

    pathEntities() {
      return {
        method: 'drive.api.files.get_entities_in_path',
        cache: ['pathEntities', this.entityName],
        params: {
          entity_name: this.entityName,
          shared: true,
        },
        onSuccess(data) {
          let breadcrumbs = [{
            label: 'Shared With Me',
            route: '/shared',
          }]
          data.forEach((entity) => {
            breadcrumbs.push({
              label: entity.title,
              route: `/shared/folder/${entity.name}`,
            })
          })
          if (breadcrumbs.length > 4) {
            breadcrumbs.splice(1, breadcrumbs.length - 4, {
              label: '...',
              route: '',
            })
          }
          this.breadcrumbs = breadcrumbs
        },
        auto: Boolean(this.entityName),
      }
    },

  },
}
</script>
