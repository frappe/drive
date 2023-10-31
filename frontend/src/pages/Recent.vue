<template>
  <div class="h-full w-full p-4">
    <FolderContentsError
      v-if="$resources.recentDriveEntity.error"
      :error="$resources.recentDriveEntity.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folder-contents="$resources.recentDriveEntity.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @close-context-menu-event="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :action-loading="actionLoading"
          :show-info-button="showInfoButton"
          :show-upload-button="false" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="`You haven't viewed any files recently`"
          :secondary-message="'Files will appear here for easy access when you view them'" />
      </template>
    </GridView>

    <ListView
      v-else
      :folder-contents="$resources.recentDriveEntity.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @close-context-menu-event="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :action-loading="actionLoading"
          :show-info-button="showInfoButton"
          :show-upload-button="false" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="`You haven't viewed any files recently`"
          :secondary-message="'Files will appear here for easy access when you view them'" />
      </template>
    </ListView>
    <EntityContextMenu
      v-if="showEntityContext"
      v-on-outside-click="closeContextMenu"
      :action-items="actionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
    <RenameDialog
      v-if="showRenameDialog"
      v-model="showRenameDialog"
      :entity="selectedEntities[0]"
      @success="
        () => {
          $resources.recentDriveEntity.fetch();
          showRenameDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-if="showUnshareDialog"
      v-model="showUnshareDialog"
      :entities="selectedEntities"
      :for="'unshare'"
      @success="
        () => {
          $resources.recentDriveEntity.fetch();
          showUnshareDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-if="showRemoveDialog"
      v-model="showRemoveDialog"
      :entities="selectedEntities"
      :for="'remove'"
      @success="
        () => {
          $resources.recentDriveEntity.fetch();
          showRemoveDialog = false;
          selectedEntities = [];
        }
      " />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="selectedEntities[0].name"
      @success="$resources.recentDriveEntity.fetch()" />
    <div />
  </div>
</template>

<script>
import ListView from "@/components/ListView.vue";
import GridView from "@/components/GridView.vue";
import DriveToolBar from "@/components/DriveToolBar.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";
import { entries, get, clear } from "idb-keyval";
import RenameDialog from "@/components/RenameDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import { getLink } from "@/utils/getLink";

export default {
  name: "Recent",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    FolderContentsError,
    EntityContextMenu,
    RenameDialog,
    ShareDialog,
    GeneralDialog,
  },
  data: () => ({
    previewEntity: null,
    showPreview: false,
    showEntityContext: false,
    entityContext: {},
    entities: [],
    actionLoading: false,
    showRenameDialog: false,
    showShareDialog: false,
    showRemoveDialog: false,
    showUnshareDialog: false,
    selectedEntities: [],
    breadcrumbs: [{ label: "Recents", route: "/recent" }],
  }),

  computed: {
    showInfoButton() {
      return !!this.selectedEntities.length && !this.$store.state.showInfo;
    },
    userId() {
      return this.$store.state.auth.user_id;
    },
    actionItems() {
      return [
        {
          label: "Preview",
          icon: "eye",
          onClick: () => {
            this.openEntity(this.selectedEntities[0]);
          },
          isEnabled: () => {
            if (this.selectedEntities.length === 1) {
              return true;
            }
          },
        },
        {
          label: "Divider",
          isEnabled: () => this.selectedEntities.length === 1,
        },
        {
          label: "Download",
          icon: "download",
          onClick: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
          },
          isEnabled: () => {
            if (this.selectedEntities.length === 1) {
              if (
                this.selectedEntities[0].allow_download ||
                this.selectedEntities[0].owner === "me"
              ) {
                return !this.selectedEntities[0].document;
              }
            }
          },
        },
        {
          label: "Share",
          icon: "share-2",
          onClick: () => {
            this.showShareDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              this.selectedEntities.every((x) => x.owner === "me")
            );
          },
        },
        {
          label: "Get Link",
          icon: "link",
          onClick: () => {
            getLink(this.selectedEntities[0]);
          },
          isEnabled: () => {
            return this.selectedEntities.length === 1;
          },
        },

        {
          label: "Divider",
          isEnabled: () => this.selectedEntities.length === 1,
        },
        {
          label: "Rename",
          icon: "edit",
          onClick: () => {
            this.showRenameDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              (this.selectedEntities[0].write ||
                this.selectedEntities[0].owner === "me")
            );
          },
        },
        {
          label: "Cut",
          icon: "scissors",
          onClick: () => {
            this.$store.commit("setPasteData", {
              entities: this.selectedEntities.map((x) => x.name),
              action: "cut",
            });
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner === "me")
            );
          },
        },
        {
          label: "Copy",
          icon: "copy",
          onClick: () => {
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
          label: "Show Info",
          icon: "info",
          onClick: () => {
            this.$store.commit("setShowInfo", true);
          },
          isEnabled: () => {
            return (
              !this.$store.state.showInfo && this.selectedEntities.length === 1
            );
          },
        },
        {
          label: "Hide Info",
          icon: "info",
          onClick: () => {
            this.$store.commit("setShowInfo", false);
          },
          isEnabled: () => {
            return this.$store.state.showInfo;
          },
        },
        {
          label: "Favourite",
          icon: "star",
          onClick: () => {
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
          label: "Unfavourite",
          icon: "star",
          onClick: () => {
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
          label: "Divider",
          isEnabled: () => true,
        },
        {
          label: "Remove from recent",
          icon: "trash-2",
          danger: true,
          onClick: () => {
            this.$resources.clearRecent.submit();
          },
          isEnabled: () => {
            return this.selectedEntities.length > 0;
          },
        },
        {
          label: "Delete",
          icon: "trash-2",
          danger: true,
          onClick: () => {
            this.showRemoveDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner === "me")
            );
          },
        },
      ].filter((item) => item.isEnabled());
    },
    columnHeaders() {
      return [
        {
          label: "Name",
          field: "title",
          sortable: false,
        },
        {
          label: "Owner",
          field: "owner",
          sortable: false,
        },
        {
          label: "Last Accessed",
          field: "modified",
          sortable: false,
        },
        {
          label: "Size",
          field: "file_size",
          sortable: false,
        },
      ].filter((item) => item.sortable);
    },
  },
  mounted() {
    /* Triggered from the navbar component */
    this.emitter.on("fetchRecents", () => {
      this.selectedEntities = [];
      this.$resources.recentDriveEntity.fetch();
    });
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
        this.$router.push({
          name: "File",
          params: { entityName: entity.name },
        });
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
    recentDriveEntity() {
      return {
        url: "drive.api.files.list_recents",
        params: {
          order_by: this.orderBy,
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation",
        },
        onSuccess(data) {
          this.$resources.recentDriveEntity.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? ""
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = entity.owner === this.userId ? "me" : entity.owner;
          });
        },
        auto: true,
      };
    },
    clearRecent() {
      return {
        url: "drive.api.files.remove_recents",
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities?.map((entity) => entity.name)
          ),
        },
        onSuccess() {
          this.$resources.recentDriveEntity.fetch();
          this.selectedEntities = [];
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
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
          this.$resources.recentDriveEntity.fetch();
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
