<template>
  <div class="h-full w-full p-4">
    <FolderContentsError
      v-if="$resources.folderContents.error"
      :error="$resources.folderContents.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folder-contents="$resources.folderContents.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @close-context-menu-event="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders"
          :action-loading="actionLoading"
          :show-info-button="showInfoButton"
          :show-upload-button="false" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="`You haven't favourited any items`"
          :secondary-message="'Items will appear here for easy access when you add them to favourites'" />
      </template>
    </GridView>

    <ListView
      v-else
      :folder-contents="$resources.folderContents.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entitycontext="(event) => toggleEntityContext(event)"
      @close-context-menu-event="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders"
          :action-loading="actionLoading"
          :show-info-button="showInfoButton"
          :show-upload-button="false" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="`You haven't favourited any items`"
          :secondary-message="'Items will appear here for easy access when you add them to favourites'" />
      </template>
    </ListView>
    <EntityContextMenu
      v-if="showEntityContext"
      v-on-outside-click="closeContextMenu"
      :action-items="actionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
    <FilePreview
      v-if="showPreview"
      :preview-entity="previewEntity"
      @hide="hidePreview" />

    <RenameDialog
      v-model="showRenameDialog"
      :entity="selectedEntities[0]"
      @success="
        () => {
          $resources.folderContents.fetch();
          showRenameDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-model="showUnshareDialog"
      :entities="selectedEntities"
      :for="'unshare'"
      @success="
        () => {
          $resources.folderContents.fetch();
          showUnshareDialog = false;
          selectedEntities = [];
        }
      " />
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
      " />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="selectedEntities[0].name"
      @success="$resources.folderContents.fetch()" />
    <div />
  </div>
</template>

<script>
import DriveToolBar from "@/components/DriveToolBar.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import GridView from "@/components/GridView.vue";
import ListView from "@/components/ListView.vue";
import FilePreview from "@/components/FilePreview.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatDate, formatSize } from "@/utils/format";

export default {
  name: "Favourites",
  components: {
    ListView,
    GridView,
    FilePreview,
    DriveToolBar,
    GeneralDialog,
    RenameDialog,
    ShareDialog,
    NoFilesSection,
    FolderContentsError,
    EntityContextMenu,
  },
  data: () => ({
    selectedEntities: [],
    previewEntity: null,
    showPreview: false,
    breadcrumbs: [{ label: "Favourites", route: "/favourites" }],
    actionLoading: false,
    showRenameDialog: false,
    showShareDialog: false,
    showUnshareDialog: false,
    showRemoveDialog: false,
    showEntityContext: false,
    entityContext: {},
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
    actionItems() {
      return [
        {
          label: "Download",
          icon: "download",
          handler: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
          },
          isEnabled: () => {
            if (this.selectedEntities.length === 1) {
              if (
                this.selectedEntities.length === 1 &&
                !this.selectedEntities[0].is_group
              ) {
                return !this.selectedEntities[0].document;
              }
            }
          },
        },
        // {
        //   label: 'Share',
        //   icon: 'share-2',
        //   handler: () => {
        //     this.showShareDialog = true;
        //   },
        //   isEnabled: () => {
        //     return (
        //       this.selectedEntities.length === 1 &&
        //       this.selectedEntities[0].write
        //     );
        //   },
        // },
        {
          label: "View details",
          icon: "eye",
          handler: () => {
            this.$store.commit("setShowInfo", true);
          },
          isEnabled: () => {
            return (
              !this.$store.state.showInfo && this.selectedEntities.length === 1
            );
          },
        },
        {
          label: "Hide details",
          icon: "eye-off",
          handler: () => {
            this.$store.commit("setShowInfo", false);
          },
          isEnabled: () => {
            return this.$store.state.showInfo;
          },
        },
        {
          label: "Rename",
          icon: "edit",
          handler: () => {
            this.showRenameDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              this.selectedEntities[0].write
            );
          },
        },
        {
          label: "Remove from Favourites",
          icon: "x-circle",
          handler: () => {
            this.$resources.toggleFavourite.submit();
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0;
          },
        },
        // {
        //   label: 'Remove',
        //   icon: 'trash-2',
        //   handler: () => {
        //     this.showUnshareDialog = true;
        //   },
        //   isEnabled: () => {
        //     return (
        //       this.selectedEntities.length > 0 &&
        //       this.selectedEntities.every((x) => x.owner != 'me') &&
        //       this.selectedEntities.every((x) => !x.everyone)
        //     );
        //   },
        // },
        // {
        //   label: 'Move to Trash',
        //   icon: 'trash-2',
        //   handler: () => {
        //     this.showRemoveDialog = true;
        //   },
        //   isEnabled: () => {
        //     return (
        //       this.selectedEntities.length > 0 &&
        //       this.selectedEntities.every((x) => x.owner === 'me')
        //     );
        //   },
        // },
      ].filter((item) => item.isEnabled());
    },
    columnHeaders() {
      return [
        {
          label: "Name",
          field: "title",
          sortable: true,
        },
        {
          label: "Owner",
          field: "owner",
          sortable: true,
        },
        {
          label: "Modified",
          field: "modified",
          sortable: true,
        },
        {
          label: "Size",
          field: "file_size",
          sortable: true,
        },
      ].filter((item) => item.sortable);
    },
  },

  mounted() {
    this.$store.commit("setCurrentBreadcrumbs", this.breadcrumbs);
    window.addEventListener(
      "dragover",
      function (e) {
        e = e || event;
        e.preventDefault();
      },
      false
    );
    window.addEventListener(
      "drop",
      function (e) {
        e = e || event;
        e.preventDefault();
      },
      false
    );
  },
  methods: {
    openEntity(entity) {
      if (entity.is_group) {
        this.selectedEntities = [];
        this.$router.push({
          name: "Folder",
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
  resources: {
    folderContents() {
      return {
        url: "drive.api.files.list_favourites",
        params: {
          order_by: this.orderBy,
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation",
        },
        onSuccess(data) {
          this.$resources.folderContents.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? "-"
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = entity.owner === this.userId ? "me" : entity.owner;
          });
        },
        auto: true,
      };
    },
    toggleFavourite() {
      return {
        url: "drive.api.files.add_or_remove_favourites",
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

<style>
html {
  -webkit-user-select: none;
  /* Safari */
  -ms-user-select: none;
  /* IE 10 and IE 11 */
  user-select: none;
  /* Standard syntax */
}
</style>
