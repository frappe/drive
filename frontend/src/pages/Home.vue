<template>
  <div class="h-full">
    <FolderContentsError
      v-if="$resources.folderContents.error"
      :error="$resources.folderContents.error"
    />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folderContents="$resources.folderContents.data"
      :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @showEntityContext="(event) => toggleEntityContext(event)"
      @closeContextMenuEvent="closeContextMenu"
    >
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :columnHeaders="columnHeaders"
          :showInfoButton="showInfoButton"
        />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </GridView>

    <ListView
      v-else
      :folderContents="$resources.folderContents.data"
      :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @showEntityContext="(event) => toggleEntityContext(event)"
      @closeContextMenuEvent="closeContextMenu"
    >
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :columnHeaders="columnHeaders"
          :showInfoButton="showInfoButton"
        />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </ListView>

    <FilePreview
      v-if="showPreview"
      @hide="hidePreview"
      :previewEntity="previewEntity"
    />
    <EntityContextMenu
      v-if="showEntityContext"
      :actionItems="actionItems"
      :entityContext="entityContext"
      :close="closeContextMenu"
      v-on-outside-click="closeContextMenu"
    />
    <RenameDialog
      v-model="showRenameDialog"
      :entity="selectedEntities[0]"
      @success="
        () => {
          $resources.folderContents.fetch();
          showRenameDialog = false;
          selectedEntities = [];
        }
      "
    />
    <GeneralDialog
      v-model="showRemoveDialog"
      :entities="selectedEntities"
      :for="'remove'"
      @success="
        () => {
          $resources.folderContents.fetch();
          showRemoveDialog = false;
          selectedEntities = [];
        }
      "
    />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entityName="this.selectedEntities[0].name"
      :entityTitle="this.selectedEntities[0].title"
      :isFolder="this.selectedEntities[0].is_group"
    />
    <div class="hidden" id="dropzoneElement" />
  </div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui';
import Dropzone from 'dropzone';
import ListView from '@/components/ListView.vue';
import GridView from '@/components/GridView.vue';
import DriveToolBar from '@/components/DriveToolBar.vue';
import NoFilesSection from '@/components/NoFilesSection.vue';
import FilePreview from '@/components/FilePreview.vue';
import RenameDialog from '@/components/RenameDialog.vue';
import ShareDialog from '@/components/ShareDialog.vue';
import GeneralDialog from '@/components/GeneralDialog.vue';
import FolderContentsError from '@/components/FolderContentsError.vue';
import EntityContextMenu from '@/components/EntityContextMenu.vue';
import { formatSize, formatDate } from '@/utils/format';

export default {
  name: 'Home',
  components: {
    FeatherIcon,
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    FilePreview,
    RenameDialog,
    ShareDialog,
    GeneralDialog,
    FolderContentsError,
    EntityContextMenu,
  },
  data: () => ({
    dropzone: null,
    selectedEntities: [],
    previewEntity: null,
    showPreview: false,
    showRenameDialog: false,
    showShareDialog: false,
    showRemoveDialog: false,
    showEntityContext: false,
    entityContext: {},
    breadcrumbs: [{ label: 'Home', route: '/' }],
  }),
  computed: {
    showInfoButton() {
      return !!this.selectedEntities.length && !this.$store.state.showInfo;
    },
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`;
    },
    actionItems() {
      return [
        {
          label: 'Download',
          icon: 'download',
          handler: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              !this.selectedEntities[0].is_group
            );
          },
        },
        {
          label: 'Share',
          icon: 'share-2',
          handler: () => {
            this.showShareDialog = true;
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1;
          },
        },
        {
          label: 'View details',
          icon: 'eye',
          handler: () => {
            this.$store.commit('setShowInfo', true);
          },
          isEnabled: () => {
            return (
              !this.$store.state.showInfo && this.selectedEntities.length === 1
            );
          },
        },
        {
          label: 'Hide details',
          icon: 'eye-off',
          handler: () => {
            this.$store.commit('setShowInfo', false);
          },
          isEnabled: () => {
            return this.$store.state.showInfo;
          },
        },
        {
          label: 'Rename',
          icon: 'edit',
          handler: () => {
            this.showRenameDialog = true;
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1;
          },
        },
        {
          label: 'Add to Favourites',
          icon: 'star',
          handler: () => {
            this.$resources.toggleFavourite.submit();
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => !x.is_favourite)
            );
          },
        },
        {
          label: 'Remove from Favourites',
          icon: 'x-circle',
          handler: () => {
            this.$resources.toggleFavourite.submit();
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.is_favourite)
            );
          },
        },
        {
          label: 'Move to Trash',
          icon: 'trash-2',
          handler: () => {
            this.showRemoveDialog = true;
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0;
          },
        },
      ].filter((item) => item.isEnabled());
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
      ].filter((item) => item.sortable);
    },
  },
  methods: {
    openEntity(entity) {
      if (entity.is_group) {
        this.selectedEntities = [];
        this.$router.push({
          name: 'Folder',
          params: { entityName: entity.name },
        });
      } else {
        this.previewEntity = entity;
        this.showPreview = true;
      }
    },
    hidePreview() {
      this.showPreview = false;
      this.previewEntity = null;
    },
    toggleEntityContext(event) {
      if (!event) this.showEntityContext = false;
      else {
        this.hidePreview();
        this.showEntityContext = true;
        this.entityContext = event;
      }
    },
    closeContextMenu() {
      this.showEntityContext = false;
      this.entityContext = undefined;
    },
  },

  mounted() {
    this.$store.commit('setHasWriteAccess', true);
    let componentContext = this;
    this.emitter.on('fetchFolderContents', () => {
      componentContext.$resources.folderContents.fetch();
    });
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
        formData.append('parent', file.parent);
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
          };
        }
      },
    });
    this.dropzone.on('addedfile', function (file) {
      file.parent = '';
      componentContext.$store.commit('pushToUploads', {
        uuid: file.upload.uuid,
        name: file.name,
        progress: 0,
      });
    });
    this.dropzone.on('uploadprogress', function (file, progress) {
      componentContext.$store.commit('updateUpload', {
        uuid: file.upload.uuid,
        progress: progress,
      });
    });
    this.dropzone.on('error', function (file, message, xhr) {
      let error_message;
      if (message._server_messages) {
        error_message = JSON.parse(message._server_messages)
          .map((element) => JSON.parse(element).message)
          .join('\n');
      }
      error_message = error_message || 'Upload failed';
      componentContext.$store.commit('updateUpload', {
        uuid: file.upload.uuid,
        error: error_message,
      });
    });
    this.dropzone.on('complete', function (file) {
      componentContext.$resources.folderContents.fetch();
      componentContext.$store.commit('updateUpload', {
        uuid: file.upload.uuid,
        completed: true,
      });
    });
    this.emitter.on('uploadFile', () => {
      if (componentContext.dropzone.hiddenFileInput)
        componentContext.dropzone.hiddenFileInput.click();
    });
  },
  unmounted() {
    this.$store.commit('setHasWriteAccess', false);
    this.dropzone.destroy();
  },
  resources: {
    folderContents() {
      return {
        method: 'drive.api.files.list_folder_contents',
        params: {
          order_by: this.orderBy,
          fields:
            'name,title,is_group,owner,modified,file_size,mime_type,creation',
        },
        onSuccess(data) {
          this.$resources.folderContents.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? '-'
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = 'me';
          });
        },
        auto: true,
      };
    },

    toggleFavourite() {
      return {
        method: 'drive.api.files.add_or_remove_favourites',
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities?.map((entity) => entity.name)
          ),
        },
        onSuccess() {
          this.$resources.folderContents.fetch();
          this.selectedEntities = [];
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
  },
};
</script>
