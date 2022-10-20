<template>
  <div class="h-full flex flex-col">
    <FolderContentsError v-if="$resources.folderContents.error" :error="$resources.folderContents.error" />

    <GridView v-else-if="$store.state.view === 'grid'" :folderContents="$resources.folderContents.data"
      @entitySelected="(selected) => (selectedEntities = selected)" :selectedEntities="selectedEntities"
      @openEntity="(entity) => openEntity(entity)" @showEntityContext="(event) => (toggleEntityContext(event))"
      @closeContextMenuEvent="closeContextMenu">
      <template #toolbar>
        <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" />
      </template>
      <template #placeholder>
        <NoFilesSection secondaryMessage="No files have been shared with you" />
      </template>
    </GridView>

    <ListView v-else :folderContents="$resources.folderContents.data"
      @entitySelected="(selected) => (selectedEntities = selected)" :selectedEntities="selectedEntities"
      @openEntity="(entity) => openEntity(entity)">
      <template #toolbar>
        <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" />
      </template>
      <template #placeholder>
        <NoFilesSection secondaryMessage="No files have been shared with you" />
      </template>
    </ListView>

    <FilePreview v-if="showPreview" @hide="hidePreview" :previewEntity="previewEntity" />
    <EntityContextMenu v-if="showEntityContext" :actionItems="actionItems" :entityContext="entityContext"
      v-on-outside-click="closeContextMenu" />
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
    <DeleteDialog v-model="showDeleteDialog" :entities="selectedEntities" @success="
      () => {
        $resources.folderContents.fetch()
        showDeleteDialog = false
        selectedEntities = []
      }
    " />
    <div class="hidden" id="dropzoneElement" />
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
import DeleteDialog from '@/components/DeleteDialog.vue'
import EntityContextMenu from '@/components/EntityContextMenu.vue'
import { formatSize, formatDate } from '@/utils/format'
import Dropzone from 'dropzone'

export default {
  name: 'Shared',
  components: {
    FeatherIcon,
    ListView,
    GridView,
    DriveToolBar,
    RenameDialog,
    GeneralDialog,
    DeleteDialog,
    NoFilesSection,
    FilePreview,
    FolderContentsError,
    EntityContextMenu,
  },
  data: () => ({
    dropzone: null,
    previewEntity: null,
    showPreview: false,
    showRenameDialog: false,
    showRemoveDialog: false,
    showDeleteDialog: false,
    showEntityContext: false,
    entityContext: {},
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
            this.closeContextMenu()
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
              this.selectedEntities.length > 0 && !this.entityName
            )
          },
        },
        {
          label: 'Remove',
          handler: () => {
            this.showDeleteDialog = true
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 && this.entityName && this.selectedEntities.every(x => x.write || x.owner === 'me')
            )
          },
        },
      ].filter((item) => item.isEnabled())
    },
  },

  methods: {
    initializeDropzone() {
      let componentContext = this
      this.dropzone = new Dropzone(this.$el.parentNode, {
        paramName: 'file',
        parallelUploads: 1,
        clickable: '#dropzoneElement',
        previewsContainer: '#dropzoneElement',
        chunking: true,
        forceChunking: true,
        url: '/api/method/drive.api.files.upload_file',
        maxFilesize: 10 * 1024, // 10GB
        chunkSize: 5 * 1024 * 1024, // 5MB
        headers: {
          'X-Frappe-CSRF-Token': window.csrf_token,
          Accept: 'application/json',
        },
        sending: function (file, xhr, formData, chunk) {
          formData.append('parent', file.parent)
        },
        params: function (files, xhr, chunk) {
          if (chunk) {
            return {
              uuid: chunk.file.upload.uuid,
              chunk_index: chunk.index,
              total_file_size: chunk.file.size,
              chunk_size: this.options.chunkSize,
              total_chunk_count: chunk.file.upload.totalChunkCount,
              chunk_byte_offset: chunk.index * this.options.chunkSize,
            }
          }
        },
      })
      this.dropzone.on('addedfile', function (file) {
        file.parent = componentContext.entityName
        componentContext.$store.commit('pushToUploads', {
          uuid: file.upload.uuid,
          name: file.name,
          progress: 0,
        })
      })
      this.dropzone.on('uploadprogress', function (file, progress) {
        componentContext.$store.commit('updateUpload', {
          uuid: file.upload.uuid,
          progress: progress,
        })
      })
      this.dropzone.on('error', function (file, message, xhr) {
        let error_message
        if (message._server_messages) {
          error_message = JSON.parse(message._server_messages)
            .map((element) => JSON.parse(element).message)
            .join('\n')
        }
        error_message = error_message || 'Upload failed'
        componentContext.$store.commit('updateUpload', {
          uuid: file.upload.uuid,
          error: error_message,
        })
      })
      this.dropzone.on('complete', function (file) {
        componentContext.$resources.folderContents.fetch()
        componentContext.$store.commit('updateUpload', {
          uuid: file.upload.uuid,
          completed: true,
        })
      })
      this.emitter.on('uploadFile', () => {
        if (componentContext.dropzone.hiddenFileInput)
          componentContext.dropzone.hiddenFileInput.click()
      })
    },
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
    toggleEntityContext(event) {
      this.hidePreview()
      this.showEntityContext = true
      this.entityContext = event
    },
    closeContextMenu() {
      this.showEntityContext = false
      this.entityContext = undefined
    },
  },

  watch: {
    async entityName(newEntityName) {
      await this.$resources.folderAccess.fetch()
      this.$store.commit('setHasWriteAccess', !!this.$resources.folderAccess.data?.write)
      this.selectedEntities = []
      if (!newEntityName) {
        this.breadcrumbs = [{ label: 'Shared With Me', route: '/shared' }]
        this.dropzone.destroy()
        this.dropzone = null
      }
      else if (!this.dropzone)
        this.initializeDropzone()
    },
    showPreview() {
      this.closeContextMenu()
    },
    showRenameDialog() {
      this.closeContextMenu()
    },
    showShareDialog() {
      this.closeContextMenu()
    },
    showRemoveDialog() {
      this.closeContextMenu()
    }
  },

  async mounted() {
    await this.$resources.folderAccess.fetch()
    this.$store.commit('setHasWriteAccess', !!this.$resources.folderAccess.data?.write)
    let componentContext = this
    this.emitter.on('fetchFolderContents', () => {
      componentContext.$resources.folderContents.fetch()
    })
    if (this.entityName) this.initializeDropzone()
  },

  unmounted() {
    if (this.dropzone) this.dropzone.destroy()
  },

  resources: {
    folderAccess() {
      return {
        method: 'drive.api.permissions.get_user_access',
        params: { entity_name: this.entityName, },
      }
    },

    folderContents() {
      return {
        method: 'drive.api.permissions.get_shared_with_me',
        // cache: ['folderContents', this.userId, this.entityName],
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
