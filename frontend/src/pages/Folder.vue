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
      :entityName="shareName"
      :entityTitle="shareTitle"
      :isFolder="shareIsFolder"
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
    showRenameDialog: false,
    showShareDialog: false,
    showRemoveDialog: false,
    showEntityContext: false,
    entityContext: {},
    breadcrumbs: [{ label: 'Home', route: '/' }],
    shareTitle: '',
  }),
  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
    showInfoButton() {
      return !!this.selectedEntities.length && !this.$store.state.showInfo;
    },
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`;
    },
    shareName() {
      return this.selectedEntities[0]
        ? this.selectedEntities[0].name
        : this.entityName;
    },
    shareIsFolder() {
      return this.selectedEntities[0] ? this.selectedEntities[0].is_group : 1;
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
            this.shareTitle = this.selectedEntities.length
              ? this.selectedEntities[0].title
              : this.breadcrumbs.at(-1).label;
            this.showShareDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 ||
              (this.entityName && !this.selectedEntities.length)
            );
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
  watch: {
    async entityName() {
      await this.$resources.folderAccess.fetch();
      this.$store.commit(
        'setHasWriteAccess',
        !!this.$resources.folderAccess.data?.write
      );
      this.selectedEntities = [];
    },
  },

  async mounted() {
    await this.$resources.folderAccess.fetch();
    this.$store.commit(
      'setHasWriteAccess',
      !!this.$resources.folderAccess.data?.write
    );
    let componentContext = this;
    this.emitter.on('fetchFolderContents', () => {
      componentContext.$resources.folderContents.fetch();
    });
  },

  unmounted() {
    this.$store.commit('setHasWriteAccess', false);
  },
  resources: {

    folderAccess() {
      return {
        method: 'drive.api.permissions.get_user_access',
        params: { entity_name: this.entityName },
      };
    },

    folderContents() {
      return {
        method: 'drive.api.files.list_folder_contents',
        // cache: ['folderContents', this.entityName],
        params: {
          entity_name: this.entityName,
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
            entity.owner = entity.owner === this.userId ? 'me' : entity.owner;
          });
        },
        auto: true,
      };
    },

    pathEntities() {
      return {
        method: 'drive.api.files.get_entities_in_path',
        // cache: ['pathEntities', this.entityName],
        params: {
          entity_name: this.entityName,
        },
        onSuccess(data) {
          let breadcrumbs = [];
          if (data.is_shared)
            breadcrumbs.push({
              label: 'Shared With Me',
              route: '/shared',
            });
          data.entities.forEach((entity, index) => {
            if (index === 0) {
              const isHome = entity.owner === this.userId;
              breadcrumbs.push({
                label: isHome ? 'Home' : entity.title,
                route: isHome ? '/' : `/folder/${entity.name}`,
              });
            } else {
              breadcrumbs.push({
                label: entity.title,
                route: `/folder/${entity.name}`,
              });
            }
          });
          if (breadcrumbs.length > 4) {
            breadcrumbs.splice(1, breadcrumbs.length - 4, {
              label: '...',
              route: '',
            });
          }
          this.breadcrumbs = breadcrumbs;
        },
        auto: Boolean(this.entityName),
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
