<template>
  <div>
    <ListView
      :entityName="entityName"
      :actionItems="actionItems"
      :folderContents="$resources.folderContents.data"
      :breadcrumbs="breadcrumbs"
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
      :show="showNewFolderDialog"
      :parent="entityName"
      @close="showNewFolderDialog = false"
      @success="
        () => {
          $resources.folderContents.fetch()
          showNewFolderDialog = false
        }
      "
    />
    <div class="hidden" id="dropzoneElement" />
  </div>
</template>

<script>
import Dropzone from 'dropzone'
import ListView from '@/components/ListView.vue'
import FilePreview from '@/components/FilePreview.vue'
import NewFolderDialog from '@/components/NewFolderDialog.vue'

export default {
  name: 'Home',
  components: {
    ListView,
    FilePreview,
    NewFolderDialog,
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
    previewEntity: '',
    selectedEntities: [],
    showNewFolderDialog: false,
    dropzone: null,
  }),
  computed: {
    userId() {
      return this.$store.state.auth.user_id
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
      ].filter((item) => item.isEnabled())
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
    openEntity(entity) {
      if (entity.is_group) {
        this.$router.push({
          name: 'Folder',
          params: { entityName: entity.name },
        })
      } else {
        this.previewEntity = entity.name
        this.showPreview = true
      }
    },
    hidePreview() {
      this.showPreview = false
      this.previewEntity = ''
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
  mounted() {
    let componentContext = this
    this.dropzone = new Dropzone(this.$el.parentNode, {
      paramName: 'file',
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
      let server_messages = JSON.parse(message._server_messages).map(
        (element) => JSON.parse(element).message
      )
      componentContext.$store.commit('updateUpload', {
        uuid: file.upload.uuid,
        error: server_messages.join('\n'),
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
