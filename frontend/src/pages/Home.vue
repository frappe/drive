<template>
  <div class="h-full">
    <FolderContentsError v-if="$resources.folderContents.error" :error="$resources.folderContents.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folderContents="$resources.folderContents.data"
      :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @showEntityContext="(event) => (toggleEntityContext(event))"
      @closeContextMenuEvent="closeContextMenu"
    >
      <template #toolbar>
        <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :columnHeaders="columnHeaders"
          @uploadFile="dropzone.hiddenFileInput.click()" :actionLoading="actionLoading"
          :showInfoButton="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </GridView>

    <ListView v-else :folderContents="$resources.folderContents.data" :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)" @openEntity="(entity) => openEntity(entity)">
      <template #toolbar>
        <DriveToolBar :actionItems="actionItems" :breadcrumbs="breadcrumbs" :columnHeaders="columnHeaders"
          @uploadFile="dropzone.hiddenFileInput.click()" :actionLoading="actionLoading"
          :showInfoButton="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </ListView>

    <FilePreview v-if="showPreview" @hide="hidePreview" :previewEntity="previewEntity" />
    <EntityContextMenu
      v-if="hideEntityContext"
      :actionItems="actionItems"
      :entityContext="entityContext"
      v-on-outside-click="closeContextMenu"
    />
    <NewFolderDialog v-model="showNewFolderDialog" :parent="entityName" @success="
      () => {
        $resources.folderContents.fetch()
        showNewFolderDialog = false
      }
    " />
    <RenameDialog v-model="showRenameDialog" :entity="selectedEntities[0]" @success="
      () => {
        $resources.folderContents.fetch()
        showRenameDialog = false
        selectedEntities = []
      }
    " />
    <GeneralDialog v-model="showRemoveDialog" :entities="selectedEntities" :for="'remove'" @success="
      () => {
        $resources.folderContents.fetch()
        showRemoveDialog = false
        selectedEntities = []
      }
    " />
    
    <ShareDialog v-if="showShareDialog" v-model="showShareDialog" :entityName="shareName" :isFolder="shareIsFolder" />
    <DetailsDialog v-model="showDetailsDialog" :entity="selectedEntities[0]" />
    <div class="hidden" id="dropzoneElement" />
  </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import Dropzone from 'dropzone'
import ListView from '@/components/ListView.vue'
import GridView from '@/components/GridView.vue'
import DriveToolBar from '@/components/DriveToolBar.vue'
import NoFilesSection from '@/components/NoFilesSection.vue'
import FilePreview from '@/components/FilePreview.vue'
import NewFolderDialog from '@/components/NewFolderDialog.vue'
import RenameDialog from '@/components/RenameDialog.vue'
import ShareDialog from '@/components/ShareDialog.vue'
import DetailsDialog from '@/components/DetailsDialog.vue'
import GeneralDialog from '@/components/GeneralDialog.vue'
import FolderContentsError from '@/components/FolderContentsError.vue'
import EntityContextMenu from '@/components/EntityContextMenu.vue'
import { formatSize, formatDate } from '@/utils/format'

export default {
  name: 'Home',
  components: {
    FeatherIcon,
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    FilePreview,
    NewFolderDialog,
    RenameDialog,
    ShareDialog,
    DetailsDialog,
    GeneralDialog,
    FolderContentsError,
    EntityContextMenu,
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: '',
    },
  },
  data: () => ({
    dropzone: null,
    selectedEntities: [],
    previewEntity: null,
    showPreview: false,
    showNewFolderDialog: false,
    showRenameDialog: false,
    showShareDialog: false,
    showDetailsDialog: false,
    showRemoveDialog: false,
    hideEntityContext: false,
    entityContext: {},
    breadcrumbs: [{ label: 'Home', route: '/' }],
    actionLoading: false,
  }),
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    showInfoButton() {
      return this.selectedEntities.length === 1
    },
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`
    },
    shareName() {
      return this.selectedEntities[0]?.name ? this.selectedEntities[0].name : this.entityName
    },
    shareIsFolder() {
      return this.selectedEntities[0]?.is_group ? this.selectedEntities[0].is_group : 1
    },
    actionItems() {
      return [
        {
          label: 'New Folder',
          handler: () => {
            this.showNewFolderDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length === 0
          },
        },
        {
          label: 'Download',
          handler: () => {
            this.closeContextMenu()
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              !this.selectedEntities[0].is_group
            )
          },
        },
        {
          label: 'Share',
          handler: () => {
            this.showShareDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1 || (this.entityName && !this.selectedEntities.length)
          },
        },
        {
          label: 'Details',
          handler: () => {
            this.showDetailsDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1
          },
        },
        {
          label: 'Rename',
          handler: () => {
            this.showRenameDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1
          },
        },
        {
          label: 'Add to Favourites',
          handler: () => {
            this.$resources.toggleFavourite.submit()
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0 && this.selectedEntities.every(x => !x.is_favourite)
          },
        },
        {
          label: 'Remove from Favourites',
          handler: () => {
            this.$resources.toggleFavourite.submit()
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0 && this.selectedEntities.every(x => x.is_favourite)
          },
        },
        {
          label: 'Move to Trash',
          handler: () => {
            this.showRemoveDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0
          },
        },
      ].filter((item) => item.isEnabled())
    },
    columnHeaders() {
      return [
        {
          label: 'Name',
          field: 'title',
          sortable: true,
        },
        {
          label: 'Owner',
          field: 'owner',
          sortable: true,
        },
        {
          label: 'Modified',
          field: 'modified',
          sortable: true,
        },
        {
          label: 'Size',
          field: 'file_size',
          sortable: true,
        },
      ].filter((item) => item.sortable)
    },
  },
  methods: {
    openEntity(entity) {
      if (entity.is_group) {
        this.selectedEntities = []
        this.$router.push({
          name: 'Folder',
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
      this.hideEntityContext = true
      this.entityContext = event
    },
    closeContextMenu(){
      this.hideEntityContext = false
      this.entityContext = undefined
    },
  },
  watch: {
    entityName(newEntityName) {
      this.selectedEntities = []
      if (!newEntityName) {
        this.breadcrumbs = [{ label: 'Home', route: '/' }]
      }
    },
    showPreview(){
      this.closeContextMenu()
    },
    showDetailsDialog(){
      this.closeContextMenu()
    },
    showRenameDialog(){
      this.closeContextMenu()
    },
    showShareDialog(){
      this.closeContextMenu()
    },
    showRemoveDialog(){
      this.closeContextMenu()
    }
  },
  mounted() {
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
  },
  unmounted() {
    this.dropzone.destroy()
  },
  resources: {
    folderContents() {
      return {
        method: 'drive.api.files.list_folder_contents',
        // cache: ['folderContents', this.entityName],
        params: {
          entity_name: this.entityName,
          order_by: this.orderBy,
          fields: 'name,title,is_group,owner,modified,file_size,mime_type,creation,is_favourite,',
        },
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
        },
        onSuccess(data) {
          let breadcrumbs = []
          data.forEach((entity, index) => {
            if (index === 0) {
              const isHome = entity.owner === this.userId
              breadcrumbs.push({
                label: isHome ? 'Home' : entity.title,
                route: isHome ? '/' : `/folder/${entity.name}`,
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
          this.breadcrumbs = breadcrumbs
        },
        auto: Boolean(this.entityName),
      }
    },

    toggleFavourite() {
      return {
        method: 'drive.api.files.favourite_entities',
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities?.map((entity) => entity.name)
          ),
        },
        onSuccess() {
          this.$resources.folderContents.fetch()
          this.selectedEntities = []
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      }
    },
  },
}
</script>
