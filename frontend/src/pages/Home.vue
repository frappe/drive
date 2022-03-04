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
      v-else
      :entityName="entityName"
      :actionItems="actionItems"
      :folderContents="$resources.folderContents.data"
      :breadcrumbs="breadcrumbs"
      :columnHeaders="columnHeaders"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @uploadFile="dropzone.hiddenFileInput.click()"
    />
    <FilePreview
      v-if="showPreview"
      @hide="hidePreview"
      :previewEntity="previewEntity"
    />
    <NewFolderDialog
      v-model="showNewFolderDialog"
      :parent="entityName"
      @success="
        () => {
          $resources.folderContents.fetch()
          showNewFolderDialog = false
        }
      "
    />
    <RenameDialog
      v-model="showRenameDialog"
      :entity="entityToRename"
      @success="
        () => {
          $resources.folderContents.fetch()
          showRenameDialog = false
        }
      "
    />
    <div class="hidden" id="dropzoneElement" />
  </div>
</template>

<script>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import Dropzone from 'dropzone'
import ListView from '@/components/ListView.vue'
import FilePreview from '@/components/FilePreview.vue'
import NewFolderDialog from '@/components/NewFolderDialog.vue'
import RenameDialog from '@/components/RenameDialog.vue'

export default {
  name: 'Home',
  components: {
    FeatherIcon,
    ListView,
    FilePreview,
    NewFolderDialog,
    RenameDialog,
  },
  provide() {
    return {
      actionItems: computed(() => this.actionItems),
      breadcrumbs: computed(() => this.breadcrumbs),
      columnHeaders: computed(() => this.columnHeaders),
    }
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: '',
    },
  },
  data: () => ({
    showPreview: false,
    previewEntity: null,
    selectedEntities: [],
    showNewFolderDialog: false,
    entityToRename: null,
    showRenameDialog: false,
    dropzone: null,
    breadcrumbs: [{ label: 'Home', route: '/' }],
  }),
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`
    },
    actionItems() {
      return [
        {
          label: 'New Folder',
          action: () => {
            this.showNewFolderDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length === 0
          },
        },
        {
          label: 'Delete',
          action: () => {
            this.$resources.deleteEntities.submit()
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0
          },
        },
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
        {
          label: 'Rename',
          action: () => {
            this.entityToRename = this.selectedEntities[0]
            this.showRenameDialog = true
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1
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
  watch: {
    entityName(newEntityName) {
      if (!newEntityName) {
        this.breadcrumbs = [{ label: 'Home', route: '/' }]
      }
    },
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
        cache: ['folderContents', this.entityName],
        params: {
          entity_name: this.entityName,
          order_by: this.orderBy,
        },
        onSuccess(data) {
          this.$resources.folderContents.error = null
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size
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
    deleteEntities() {
      return {
        method: 'drive.api.files.delete_entities',
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities.map((entity) => entity.name)
          ),
        },
        onSuccess() {
          this.$resources.folderContents.fetch()
          this.selectedEntities = []
        },
      }
    },
  },
}
</script>
