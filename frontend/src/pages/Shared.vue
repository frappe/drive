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
          :show-info-button="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection
          secondary-message="No files have been shared with you" />
      </template>
    </GridView>

    <ListView
      v-else
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
          :show-info-button="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection
          secondary-message="No files have been shared with you" />
      </template>
    </ListView>

    <FilePreview
      v-if="showPreview"
      :preview-entity="previewEntity"
      @hide="hidePreview" />
    <EntityContextMenu
      v-if="showEntityContext"
      v-on-outside-click="closeContextMenu"
      :action-items="actionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
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
      v-model="showRemoveDialog"
      :entities="selectedEntities"
      :for="'unshare'"
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
  </div>
</template>

<script>
import ListView from "@/components/ListView.vue";
import GridView from "@/components/GridView.vue";
import DriveToolBar from "@/components/DriveToolBar.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import FilePreview from "@/components/FilePreview.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";

export default {
  name: "Shared",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    RenameDialog,
    GeneralDialog,
    ShareDialog,
    NoFilesSection,
    FilePreview,
    FolderContentsError,
    EntityContextMenu,
  },
  data: () => ({
    previewEntity: null,
    showPreview: false,
    showRenameDialog: false,
    showShareDialog: false,
    showRemoveDialog: false,
    showEntityContext: false,
    entityContext: {},
    selectedEntities: [],
    breadcrumbs: [{ label: "Shared With Me", route: "/shared" }],
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
          label: "Download",
          icon: "download",
          handler: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              !this.selectedEntities[0].is_group &&
              (this.selectedEntities[0].allow_download ||
                this.selectedEntities[0].write)
            );
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
          label: "Copy",
          icon: "copy",
          handler: () => {
            this.$store.commit("setPasteData", {
              entities: this.selectedEntities.map((x) => x.name),
              action: "copy",
            });
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0;
          },
        },
        {
          label: "Paste into Folder",
          icon: "clipboard",
          handler: async () => {
            const method =
              this.$store.state.pasteData.action === "cut" ? "move" : "copy";
            for (
              let i = 0;
              i < this.$store.state.pasteData.entities.length;
              i++
            ) {
              await this.$resources.pasteEntity.submit({
                method,
                entity_name: this.$store.state.pasteData.entities[i],
                new_parent: this.selectedEntities[0].name,
              });
            }
            this.selectedEntities = [];
            this.$store.commit("setPasteData", { entities: [], action: null });
            this.$resources.folderContents.fetch();
          },
          isEnabled: () => {
            return (
              this.$store.state.pasteData.entities.length &&
              this.selectedEntities.length === 1 &&
              this.selectedEntities[0].is_group &&
              this.selectedEntities[0].write
            );
          },
        },
        {
          label: "Add to Favourites",
          icon: "star",
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
          label: "Remove from Favourites",
          icon: "x-circle",
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
          label: "Unshare",
          icon: "trash-2",
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
  mounted() {
    this.$store.commit("setCtaButton", {
      text: "Upload",
      prefix: "upload",
      suffix: "chevron-down",
      variant: "solid",
    });
    this.$store.commit("setCurrentBreadcrumbs", this.breadcrumbs);
  },
  resources: {
    folderContents() {
      return {
        url: "drive.api.permissions.get_shared_with_me",
        params: {
          order_by: this.orderBy,
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
          });
        },
        auto: true,
      };
    },

    pasteEntity() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        validate(params) {
          if (!params?.new_parent) {
            return "New parent is required";
          }
        },
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
