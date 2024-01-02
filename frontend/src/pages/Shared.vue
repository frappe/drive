<template>
  <div class="h-full w-full p-4">
    <FolderContentsError v-if="errorMessage" :error="errorMessage" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folder-contents="folderContent"
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
      :folder-contents="folderContent"
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
          fetchUpdate();
          showRenameDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-model="showRemoveDialog"
      :entities="selectedEntities"
      :for="this.shareView === 'with' ? 'unshare' : 'remove'"
      @success="
        () => {
          fetchUpdate();
          showRemoveDialog = false;
          selectedEntities = [];
        }
      " />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="selectedEntities[0].name"
      @success="
        () => {
          fetchUpdate();
          showShareDialog = false;
          selectedEntities = [];
        }
      " />
  </div>
</template>

<script>
import ListView from "@/components/ListView.vue";
import GridView from "@/components/GridView.vue";
import DriveToolBar from "@/components/DriveToolBar.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";
import {
  folderDownload,
  selectedEntitiesDownload,
} from "@/utils/folderDownload";
import {
  Scan,
  FileDown,
  FolderDown,
  Share2,
  FolderInput,
  Copy,
  TextCursorInput,
  Link2,
  Info,
  Star,
  Trash2,
  FolderPlus,
  FolderUp,
  FileUp,
  FileText,
} from "lucide-vue-next";
import { Download } from "lucide-vue-next";

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
    FolderContentsError,
    EntityContextMenu,
    Scan,
    Share2,
    FolderInput,
    FileDown,
    FolderDown,
    Copy,
    TextCursorInput,
    Link2,
    Info,
    Star,
    Trash2,
    FolderPlus,
    FolderUp,
    FileUp,
    FileText,
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
    folderContent: [],
    errorMessage: null,
    breadcrumbs: [{ label: "Shared", route: "/shared" }],
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
    currentUser() {
      return this.$store.state.auth.user_id;
    },
    shareView() {
      return this.$store.state.shareView;
    },
    actionItems() {
      if (this.shareView === "with") {
        return [
          {
            label: "Download",
            icon: FileDown,
            onClick: () => {
              window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
            },
            isEnabled: () => {
              if (this.selectedEntities.length === 1) {
                if (
                  this.selectedEntities.length === 1 &&
                  !this.selectedEntities[0].is_group &&
                  (this.selectedEntities[0].allow_download ||
                    this.selectedEntities[0].write)
                ) {
                  return !this.selectedEntities[0].document;
                }
              }
            },
          },
          {
            label: "Download",
            icon: FolderDown,
            onClick: () => {
              if (this.selectedEntities.length > 1) {
                let selected_entities = this.selectedEntities;
                selectedEntitiesDownload(selected_entities);
              } else if (this.selectedEntities[0].is_group === 1) {
                folderDownload(this.selectedEntities[0]);
              }
            },
            isEnabled: () => {
              if (
                this.selectedEntities.length === 1 &&
                !this.selectedEntities[0].is_group
              ) {
                return false;
              }
              if (this.selectedEntities.length) {
                const allEntitiesSatisfyCondition = this.selectedEntities.every(
                  (entity) => {
                    return (
                      entity.allow_download ||
                      entity.write ||
                      entity.owner === "Me"
                    );
                  }
                );
                return allEntitiesSatisfyCondition;
              }
            },
          },
          {
            label: "Divider",
            isEnabled: () =>
              this.selectedEntities.length === 1 &&
              this.selectedEntities[0].allow_download === 1,
          },
          {
            label: "Share",
            icon: Share2,
            onClick: () => {
              this.showShareDialog = true;
            },
            isEnabled: () => {
              if (this.selectedEntities.length === 1) {
                if (this.selectedEntities.owner === this.currentUser) {
                  return true;
                }
              }
            },
          },
          {
            label: "Show Info",
            icon: Info,
            onClick: () => {
              this.$store.commit("setShowInfo", true);
            },
            isEnabled: () => {
              return (
                !this.$store.state.showInfo &&
                this.selectedEntities.length === 1
              );
            },
          },
          {
            label: "Hide Info",
            icon: Info,
            onClick: () => {
              this.$store.commit("setShowInfo", false);
            },
            isEnabled: () => {
              return this.$store.state.showInfo;
            },
          },
          {
            label: "Rename",
            icon: TextCursorInput,
            onClick: () => {
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
            label: "Duplicate",
            icon: Copy,
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
            label: "Paste into Folder",
            icon: "clipboard",
            onClick: async () => {
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
              this.$store.commit("setPasteData", {
                entities: [],
                action: null,
              });
              this.fetchUpdate();
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
            label: "Favourite",
            icon: Star,
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
            icon: Star,
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
            label: "Unshare",
            icon: Trash2,
            danger: true,
            onClick: () => {
              this.showRemoveDialog = true;
            },
            isEnabled: () => {
              return this.selectedEntities.length > 0;
            },
          },
        ].filter((item) => item.isEnabled());
      } else {
        /* Sane to presume the user owns all all these */
        return [
          /* Folder Download */
          {
            label: "Download",
            icon: FolderDown,
            onClick: () => {
              if (this.selectedEntities.length > 1) {
                let selected_entities = this.selectedEntities;
                selectedEntitiesDownload(selected_entities);
              } else if (this.selectedEntities[0].is_group === 1) {
                folderDownload(this.selectedEntities[0]);
              }
            },
            isEnabled: () => {
              if (
                this.selectedEntities.length === 1 &&
                !this.selectedEntities[0].is_group
              ) {
                return false;
              }
              if (this.selectedEntities.length) {
                const allEntitiesSatisfyCondition = this.selectedEntities.every(
                  (entity) => {
                    return (
                      entity.allow_download ||
                      entity.write ||
                      entity.owner === "Me"
                    );
                  }
                );
                return allEntitiesSatisfyCondition;
              }
            },
          },
          {
            label: "Download",
            icon: FileDown,
            onClick: () => {
              window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
            },
            isEnabled: () => {
              if (this.selectedEntities.length === 1) {
                if (
                  this.selectedEntities.length === 1 &&
                  !this.selectedEntities[0].is_group &&
                  !this.selectedEntities[0].document
                ) {
                  return this.selectedEntities[0].owner === "Me";
                }
              }
            },
          },
          {
            label: "Share",
            icon: Share2,
            onClick: () => {
              this.showShareDialog = true;
            },
            isEnabled: () => {
              return this.selectedEntities.length === 1;
            },
          },
          {
            label: "Show Info",
            icon: Info,
            onClick: () => {
              this.$store.commit("setShowInfo", true);
            },
            isEnabled: () => {
              return (
                !this.$store.state.showInfo &&
                this.selectedEntities.length === 1
              );
            },
          },
          {
            label: "Hide Info",
            icon: Info,
            onClick: () => {
              this.$store.commit("setShowInfo", false);
            },
            isEnabled: () => {
              return this.$store.state.showInfo;
            },
          },
          {
            label: "Rename",
            icon: TextCursorInput,
            onClick: () => {
              this.showRenameDialog = true;
            },
            isEnabled: () => {
              return this.selectedEntities.length === 1;
            },
          },
          {
            label: "Move",
            icon: FolderInput,
            onClick: () => {
              this.$store.commit("setPasteData", {
                entities: this.selectedEntities.map((x) => x.name),
                action: "cut",
              });
            },
            isEnabled: () => {
              return this.selectedEntities.length > 0;
            },
          },
          {
            label: "Favourite",
            icon: Star,
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
            icon: Star,
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
            label: "Color",
            isEnabled: () => {
              return (
                this.selectedEntities.length === 1 &&
                this.selectedEntities[0].is_group
              );
            },
          },
          {
            label: "Move to Trash",
            danger: true,
            icon: Trash2,
            onClick: () => {
              this.showRemoveDialog = true;
            },
            isEnabled: () => {
              return this.selectedEntities.length > 0;
            },
          },
        ].filter((item) => item.isEnabled());
      }
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
        {
          label: "Type",
          field: "mime_type",
          sortable: true,
        },
      ].filter((item) => item.sortable);
    },
  },
  /*   watch: {
    shareView: {
      handler(value) {
        this.fetchUpdate(value)
      },
    },
  }, */
  methods: {
    fetchUpdate() {
      this.shareView === "with"
        ? this.$resources.sharedWithMe.fetch()
        : this.$resources.sharedByMe.fetch();
    },
    openEntity(entity) {
      if (entity.is_group) {
        this.selectedEntities = [];
        this.$router.push({
          name: "Folder",
          params: { entityName: entity.name },
        });
      } else if (entity.document) {
        this.$router.push({
          name: "Document",
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
  mounted() {
    this.$store.commit("setCurrentBreadcrumbs", this.breadcrumbs);
  },
  resources: {
    sharedByMe() {
      return {
        url: "drive.api.permissions.get_shared_by_me",
        params: {
          order_by: this.orderBy,
        },
        onSuccess(data) {
          this.folderContent = [];
          this.$resources.sharedWithMe.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? ""
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            this.folderContent = data;
            entity.owner = "Me";
          });
          this.$store.commit("setCurrentViewEntites", data);
        },
        onError(error) {
          this.folderContent = [];
          if (error.messages) {
            this.errorMessage = error;
            console.log(error.messages);
          }
        },
        auto: this.shareView === "by",
      };
    },
    sharedWithMe() {
      return {
        url: "drive.api.permissions.get_shared_with_me",
        params: {
          order_by: this.orderBy,
        },
        onSuccess(data) {
          this.folderContent = [];
          this.$resources.sharedWithMe.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? ""
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            this.folderContent = data;
            this.$store.commit("setCurrentViewEntites", data);
          });
        },
        onError(error) {
          this.folderContent = [];
          if (error.messages) {
            this.errorMessage = error;
            console.log(error.messages);
          }
        },
        auto: this.shareView === "with",
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
          this.fetchUpdate();
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
