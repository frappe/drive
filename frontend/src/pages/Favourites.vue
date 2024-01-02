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
          $resources.folderContents.fetch();
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
          $resources.folderContents.fetch();
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
import GeneralDialog from "@/components/GeneralDialog.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatDate, formatSize } from "@/utils/format";
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

export default {
  name: "Favourites",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    GeneralDialog,
    RenameDialog,
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
          label: "Preview",
          icon: Scan,
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
          icon: FileDown,
          onClick: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
          },
          isEnabled: () => {
            if (this.selectedEntities.length === 1) {
              if (
                this.selectedEntities[0].allow_download ||
                this.selectedEntities[0].owner === "Me"
              ) {
                return !this.selectedEntities[0].document;
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
            return (
              this.selectedEntities.length === 1 &&
              this.selectedEntities.every((x) => x.owner === "Me")
            );
          },
        },
        {
          label: "Get Link",
          icon: Link2,
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
          icon: TextCursorInput,
          onClick: () => {
            this.showRenameDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              (this.selectedEntities[0].write ||
                this.selectedEntities[0].owner === "Me")
            );
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
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner === "Me")
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
          label: "Show Info",
          icon: Info,
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
          icon: Info,
          onClick: () => {
            this.$store.commit("setShowInfo", false);
          },
          isEnabled: () => {
            return this.$store.state.showInfo;
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
          label: "Divider",
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner === "Me")
            );
          },
        },
        {
          label: "Move to Trash",
          icon: Trash2,
          danger: true,
          onClick: () => {
            this.showRemoveDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner === "Me")
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
    this.emitter.on("fetchFavourites", () => {
      this.selectedEntities = [];
      this.$resources.folderContents.fetch();
    });
  },
  methods: {
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
              ? ""
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = entity.owner === this.userId ? "Me" : entity.owner;
          });
          this.$store.commit("setCurrentViewEntites", data);
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
