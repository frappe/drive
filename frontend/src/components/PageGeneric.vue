<template>
  <div class="h-full w-full" @contextmenu="toggleEmptyContext">
    <FolderContentsError
      v-if="$resources.folderContents.error"
      :error="$resources.folderContents.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folder-contents="folderItems"
      :selected-entities="selectedEntities"
      :overrideCanLoadMore="overrideCanLoadMore"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @show-empty-entity-context="(event) => toggleEmptyContext(event)"
      @close-context-menu-event="closeContextMenu"
      @fetch-folder-contents="() => $resources.folderContents.fetch()"
      @update-offset="fetchNextPage">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="primaryMessage"
          :secondary-message="secondaryMessage" />
      </template>
    </GridView>
    <ListView
      v-else
      :folder-contents="folderItems"
      :selected-entities="selectedEntities"
      :overrideCanLoadMore="overrideCanLoadMore"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @show-empty-entity-context="(event) => toggleEmptyContext(event)"
      @close-context-menu-event="closeContextMenu"
      @fetch-folder-contents="() => $resources.folderContents.fetch()"
      @update-offset="fetchNextPage">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders" />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </ListView>
    <EntityContextMenu
      v-if="showEntityContext"
      v-on-outside-click="closeContextMenu"
      :entity-name="selectedEntities[0].name"
      :action-items="actionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
    <EmptyEntityContextMenu
      v-if="showEmptyEntityContextMenu && allowEmptyContextMenu"
      v-on-outside-click="closeContextMenu"
      :action-items="emptyActionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
    <NewFolderDialog
      v-if="showNewFolderDialog"
      v-model="showNewFolderDialog"
      :parent="$route.params.entityName"
      @success="
        (data) => {
          // Will break if more folders exist than the pagelength
          // Need to check the sort and see where the newly created folder fits
          // And re-fetch that offset
          handleListMutation();
          showNewFolderDialog = false;
        }
      " />
    <RenameDialog
      v-if="showRenameDialog"
      v-model="showRenameDialog"
      :entity="selectedEntities[0]"
      @success="
        (data) => {
          handleListMutation(data.name);
          showRenameDialog = false;
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
          handleListMutation();
          showRemoveDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-model="showUnshareDialog"
      :entities="selectedEntities"
      :for="'unshare'"
      @success="
        () => {
          handleListMutation();
          showUnshareDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-model="showRestoreDialog"
      :entities="selectedEntities"
      :for="'restore'"
      @success="
        () => {
          handleListMutation();
          showRestoreDialog = false;
          selectedEntities = [];
        }
      " />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="selectedEntities[0].name" />
    <MoveDialog
      v-if="showMoveDialog"
      v-model="showMoveDialog"
      :entity-name="selectedEntities[0].name"
      @success="
        () => {
          handleListMutation(selectedEntities[0].name);
          showMoveDialog = false;
          selectedEntities = [];
        }
      " />
    <DeleteDialog
      v-model="showDeleteDialog"
      :entities="
        selectedEntities.length > 0
          ? selectedEntities
          : $resources.folderContents.data
      "
      @success="
        () => {
          offset = 0;
          folderItems = null;
          selectedEntities = [];
          fetchNextPage();
          showDeleteDialog = false;
        }
      " />
    <CTADeleteDialog
      v-model="showCTADelete"
      :clearAll="clearAll"
      @success="
        () => {
          offset = 0;
          folderItems = null;
          selectedEntities = [];
          fetchNextPage();
          showCTADelete = false;
        }
      " />
  </div>
</template>

<script>
import ListView from "@/components/ListView.vue";
import GridView from "@/components/GridView.vue";
import DriveToolBar from "@/components/DriveToolBar.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import NewFolderDialog from "@/components/NewFolderDialog.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import DeleteDialog from "@/components/DeleteDialog.vue";
import CTADeleteDialog from "@/components/CTADeleteDialog.vue";
import MoveDialog from "../components/MoveDialog.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";
import { getLink } from "@/utils/getLink";
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
  RotateCcw,
} from "lucide-vue-next";

export default {
  name: "PageGeneric",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    NewFolderDialog,
    RenameDialog,
    MoveDialog,
    DeleteDialog,
    ShareDialog,
    GeneralDialog,
    FolderContentsError,
    EntityContextMenu,
    EmptyEntityContextMenu,
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
    RotateCcw,
    CTADeleteDialog,
  },
  data: () => ({
    folderItems: null,
    selectedEntities: [],
    previewEntity: null,
    showPreview: false,
    showNewFolderDialog: false,
    showRenameDialog: false,
    showShareDialog: false,
    showRemoveDialog: false,
    showDeleteDialog: false,
    showUnshareDialog: false,
    showRestoreDialog: false,
    showMoveDialog: false,
    showEntityContext: false,
    showEmptyEntityContextMenu: false,
    entityContext: {},
    pageLength: 60,
    pageOffset: 0,
    overrideCanLoadMore: false,
    clearAll: false,
    showCTADelete: false,
  }),
  props: {
    url: {
      type: String,
      default: "",
      required: false,
    },
    parent: {
      type: String,
      default: null,
      required: false,
    },
    allowEmptyContextMenu: {
      type: Boolean,
      default: false,
      required: false,
    },
    isSharedFolder: {
      type: Boolean,
      default: false,
      required: false,
    },
    isActive: {
      type: Boolean,
      default: true,
      required: false,
    },
    showSort: {
      type: Boolean,
      default: false,
      required: false,
    },
    entityName: {
      type: String,
      required: false,
      default: "",
    },
    primaryMessage: {
      type: String,
      required: false,
    },
    secondaryMessage: {
      type: String,
      required: false,
    },
  },

  computed: {
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`;
    },
    userId() {
      return this.$store.state.auth.user_id;
    },
    columnHeaders() {
      if (this.showSort) {
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
      }
    },
    emptyActionItems() {
      return [
        {
          label: "Upload File",
          icon: FileUp,
          handler: () => this.emitter.emit("uploadFile"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "Upload Folder",
          icon: FolderUp,
          handler: () => this.emitter.emit("uploadFolder"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New Folder",
          icon: FolderPlus,
          handler: () => (this.showNewFolderDialog = true),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New Document",
          icon: FileText,
          handler: () => this.newDocument(),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "Paste",
          icon: "clipboard",
          handler: async () => {
            this.pasteEntities();
          },
          isEnabled: () => this.$store.state.pasteData.entities.length,
        },
      ].filter((item) => item.isEnabled());
    },
    actionItems() {
      if (this.$route.name === "Trash") {
        return [
          {
            label: "Restore",
            icon: RotateCcw,
            onClick: () => {
              this.showRestoreDialog = true;
            },
            isEnabled: () => {
              return this.selectedEntities.length > 0;
            },
          },
          {
            label: "Delete forever",
            icon: Trash2,
            danger: true,
            onClick: () => {
              this.showDeleteDialog = true;
            },
            isEnabled: () => {
              if (this.$route.name === "Trash") {
                return this.selectedEntities.length > 0;
              }
            },
          },
        ].filter((item) => item.isEnabled());
      } else {
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
                  return (
                    this.selectedEntities[0].allow_download ||
                    this.selectedEntities[0].owner === "Me"
                  );
                }
              }
            },
          },
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
                    return entity.allow_download || entity.owner === "Me";
                  }
                );
                return allEntitiesSatisfyCondition;
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
                this.selectedEntities[0].owner === "Me"
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
              this.showMoveDialog = true;
            },
            isEnabled: () => {
              const allOwned = this.selectedEntities.every((entity) => {
                return entity.owner === "Me";
              });
              return this.selectedEntities.length > 0 && allOwned;
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
              return (
                this.selectedEntities.length > 0 &&
                (this.selectedEntities[0].write ||
                  this.selectedEntities[0].owner === "Me")
              );
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
              return (
                this.$store.state.showInfo && this.selectedEntities.length === 1
              );
            },
          },
          {
            label: "Paste",
            icon: "clipboard",
            onClick: async () => {
              this.pasteEntities(this.selectedEntities[0].name);
            },
            isEnabled: () => {
              return (
                this.$store.state.pasteData.entities.length &&
                this.selectedEntities.length === 1 &&
                this.selectedEntities[0].is_group
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
            label: "Color",
            isEnabled: () => {
              return (
                this.selectedEntities.length === 1 &&
                this.selectedEntities[0].is_group &&
                (this.selectedEntities[0].write === 1 ||
                  this.selectedEntities[0].owner === "Me")
              );
            },
          },
          {
            label: "Remove from Recents",
            icon: Trash2,
            danger: true,
            onClick: () => {
              this.$resources.clearRecent.submit();
            },
            isEnabled: () => {
              if (this.$route.name === "Recents") {
                return this.selectedEntities.length > 0;
              }
            },
          },
          {
            label: "Unshare",
            danger: true,
            icon: "trash-2",
            onClick: () => {
              this.showUnshareDialog = true;
            },
            isEnabled: () => {
              return (
                this.selectedEntities.length > 0 &&
                this.selectedEntities.every((x) => x.owner != "Me") &&
                (this.selectedEntities.every((x) => x.write) ||
                  !this.isSharedFolder)
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
              const allOwned = this.selectedEntities.every((entity) => {
                return entity.owner === "Me";
              });
              return this.selectedEntities.length > 0 && allOwned;
            },
          },
        ].filter((item) => item.isEnabled());
      }
    },
  },
  watch: {
    folderItems: {
      handler(newVal, oldVal) {
        this.$store.commit("setCurrentViewEntites", newVal);
      },
    },
    orderBy: {
      handler(newVal, oldVal) {
        this.pageOffset = 0;
        this.handleListMutation();
      },
    },
  },
  mounted() {
    this.fetchNextPage();
    this.emitter.on("fetchFolderContents", () => {
      this.handleListMutation();
    });
    this.emitter.on("showCTADelete", () => {
      this.clearAll = true;
      this.showCTADelete = true;
    });
    this.emitter.on("selectAll", () => {
      this.clearAll();
    });
    this.emitter.on("createNewDocument", () => {
      this.newDocument();
    });

    this.pasteListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "v" || e.key === "V") &&
        this.$store.state.pasteData.entities.length
      )
        this.pasteEntities();
    };
    window.addEventListener("keydown", this.pasteListener);

    this.deleteListener = (e) => {
      if (e.key === "Delete" && this.selectedEntities.length)
        this.showRemoveDialog = true;
    };
    window.addEventListener("keydown", this.deleteListener);

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
    this.$store.commit("setHasWriteAccess", true);
  },
  unmounted() {
    this.folderItems = [];
    this.pageOffset = 0;
    this.emitter.off("fetchFolderContents");
    this.$store.commit("setHasWriteAccess", false);
    window.removeEventListener("keydown", this.pasteListener);
    window.removeEventListener("keydown", this.deleteListener);
  },
  methods: {
    fetchNextPage() {
      this.pageOffset = this.pageOffset + this.pageLength;
      this.$resources.folderContents.fetch().then((data) => {
        this.overrideCanLoadMore = data.length < 60 ? false : true;
        this.folderItems = this.folderItems
          ? this.folderItems.concat(data)
          : data;
      });
    },
    handleListMutation(entityID) {
      let index = this.folderItems.findIndex((obj) => obj.name === entityID);
      let entityPage = Math.ceil(index / this.pageLength);
      let entityOriginalOffset = Math.max(
        0,
        entityPage * this.pageLength - this.pageLength
      );
      this.$resources.folderContents
        .fetch({
          entity_name: this.entityName,
          order_by: this.orderBy,
          offset: entityOriginalOffset,
          limit: this.pageLength,
          is_active: this.isActive,
        })
        .then((data) => {
          this.folderItems.splice(
            entityOriginalOffset,
            entityOriginalOffset + this.pageLength,
            ...data
          );
        });
    },
    openEntity(entity) {
      if (this.$route.name === "Trash") {
        return;
      }
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
    async pasteEntities(newParent = this.$store.state.currentFolderID) {
      const method =
        this.$store.state.pasteData.action === "cut" ? "move" : "copy";
      for (let i = 0; i < this.$store.state.pasteData.entities.length; i++) {
        await this.$resources.pasteEntity.submit({
          method,
          entity_name: this.$store.state.pasteData.entities[i],
          new_parent: newParent,
        });
      }
      this.selectedEntities = [];
      this.$store.commit("setPasteData", { entities: [], action: null });
      this.$resources.folderContents.fetch();
    },
    toggleEntityContext(event) {
      if (!event) this.showEntityContext = false;
      else {
        this.showEntityContext = true;
        this.showEmptyEntityContextMenu = false;
        this.entityContext = event;
      }
    },
    toggleEmptyContext(event) {
      if (!event) {
        this.showEntityContext = false;
        this.showEmptyEntityContextMenu = false;
      } else if (this.selectedEntities.length === 0) {
        this.selectedEntities = [];
        this.showEntityContext = false;
        this.showEmptyEntityContextMenu = true;
        this.entityContext = event;
      } else if (this.selectedEntities.length > 0) {
        this.showEntityContext = true;
        this.showEmptyEntityContextMenu = false;
        this.entityContext = event;
      }
    },
    closeContextMenu() {
      this.showEntityContext = false;
      this.showEmptyEntityContextMenu = false;
      this.entityContext = undefined;
    },
    async newDocument() {
      await this.$resources.createDocument.submit({
        title: "Untitled Document",
        content: null,
        parent: this.$store.state.currentFolderID,
      });
      this.$router.push({
        name: "Document",
        params: { entityName: this.previewEntity.name },
      });
    },
  },
  resources: {
    pasteEntity() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        auto: false,
      };
    },
    folderContents() {
      return {
        method: "GET",
        url: this.url,
        auto: false,
        params: {
          entity_name: this.entityName,
          order_by: this.orderBy,
          offset: this.pageOffset,
          limit: this.pageLength,
          is_active: this.isActive,
        },
        transform(data) {
          this.$resources.folderContents.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            if (entity.is_group) {
              if (entity.item_count === 0 || entity.item_count > 0) {
                entity.file_size = entity.item_count + " item";
                if (entity.item_count > 1) {
                  entity.file_size = entity.item_count + " items";
                }
              } else {
                entity.file_size = "";
              }
            } else {
              entity.file_size = formatSize(entity.file_size);
            }
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner =
              entity.owner === this.userId ? "Me" : entity.full_name;
          });
        },
        onError(error) {
          if (error && error.exc_type === "PermissionError") {
            this.$store.commit("setError", {
              primaryMessage: "Forbidden",
              secondaryMessage: "Insufficient permissions for this resource",
            });
            this.$router.replace({ name: "Error" });
          }
        },
      };
    },
    toggleFavourite() {
      return {
        method: "POST",
        auto: false,
        url: "drive.api.files.add_or_remove_favourites",
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities?.map((entity) => entity.name)
          ),
        },
        onSuccess() {
          this.handleListMutation(this.selectedEntities[0].name);
          this.selectedEntities = [];
        },
      };
    },
    clearRecent() {
      return {
        method: "POST",
        auto: false,
        url: "drive.api.files.remove_recents",
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities?.map((entity) => entity.name)
          ),
        },
        onSuccess(dat) {
          this.handleListMutation(this.selectedEntities[0].name);
          this.selectedEntities = [];
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
    createDocument() {
      return {
        method: "POST",
        url: "drive.api.files.create_document_entity",
        onSuccess(data) {
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
          this.$store.commit("setEntityInfo", [data]);
          this.previewEntity = data;
          data.owner = "Me";
        },
        onError(error) {
          console.log(error.messages);
        },
        auto: false,
      };
    },
  },
};
</script>

<style>
html {
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
</style>
