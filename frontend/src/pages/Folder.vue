<template>
  <div class="h-full w-full p-4" @contextmenu="toggleEmptyContext">
    <FolderContentsError
      v-if="folderContents.error"
      :error="folderContents.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folder-contents="folderContents.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @show-empty-entity-context="(event) => toggleEmptyContext(event)"
      @close-context-menu-event="closeContextMenu"
      @fetch-folder-contents="() => folderContents.fetch()">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders"
          :show-info-button="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </GridView>

    <ListView
      v-else
      :folder-contents="folderContents.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @open-entity="(entity) => openEntity(entity)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @show-empty-entity-context="(event) => toggleEmptyContext(event)"
      @close-context-menu-event="closeContextMenu"
      @fetch-folder-contents="() => folderContents.fetch()">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders"
          :show-info-button="showInfoButton" />
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
      v-if="showEmptyEntityContextMenu && isLoggedIn"
      v-on-outside-click="closeContextMenu"
      :action-items="emptyActionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
    <NewFolderDialog
      v-if="showNewFolderDialog"
      v-model="showNewFolderDialog"
      :parent="$route.params.entityName"
      @success="
        () => {
          emitter.emit('fetchFolderContents');
          showNewFolderDialog = false;
        }
      " />
    <RenameDialog
      v-if="showRenameDialog"
      v-model="showRenameDialog"
      :entity="selectedEntities[0]"
      @success="
        () => {
          folderContents.fetch();
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
          folderContents.fetch();
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
          folderContents.fetch();
          showUnshareDialog = false;
          selectedEntities = [];
        }
      " />
    <ShareDialog
      v-if="showShareDialog"
      v-model="showShareDialog"
      :entity-name="shareName"
      @success="folderContents.fetch()" />
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
import FolderContentsError from "@/components/FolderContentsError.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";
import {
  folderDownload,
  selectedEntitiesDownload,
} from "@/utils/folderDownload";
import { getLink } from "@/utils/getLink";
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
  name: "Folder",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    NewFolderDialog,
    RenameDialog,
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
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: "",
    },
  },
  data: () => ({
    selectedEntities: [],
    previewEntity: null,
    showPreview: false,
    showRenameDialog: false,
    showShareDialog: false,
    showRemoveDialog: false,
    showUnshareDialog: false,
    showEntityContext: false,
    showEmptyEntityContextMenu: false,
    showNewFolderDialog: false,
    entityContext: {},
    breadcrumbs: [{ label: "Folder", route: "/folder" }],
    isSharedFolder: false,
    currentFolder: null,
  }),
  computed: {
    folderContents() {
      return this.$resources.currentFolder.data?.owner !== this.userId
        ? this.$resources.sharedEntities
        : this.$resources.ownerEntities;
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
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
    resourceURL() {
      if (this.isSharedFolder == false) {
        return "drive.api.files.list_owned_entities";
      } else {
        return "drive.api.files.list_folder_contents";
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
            this.pasteEntities(this.entityName);
          },
          isEnabled: () =>
            this.$store.state.pasteData.entities.length &&
            this.$store.state.hasWriteAccess,
        },
      ].filter((item) => item.isEnabled());
    },
    actionItems() {
      /* Owner actions */
      if (this.currentFolder?.owner === this.userId) {
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
                return (
                  !this.selectedEntities[0].is_group ||
                  !!this.selectedEntities[0].document
                );
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
                this.selectedEntities.length > 1 ||
                (this.selectedEntities.length === 1 &&
                  this.selectedEntities[0].is_group === 1)
              ) {
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
            isEnabled: () => true,
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
            label: "Cut",
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
                this.selectedEntities.every((x) => x.owner === "Me" || x.write)
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
                this.selectedEntities[0].is_group &&
                (this.selectedEntities[0].write ||
                  this.selectedEntities[0].owner === "Me")
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
                this.selectedEntities[0].is_group
              );
            },
          },
          {
            label: "Divider",
            isEnabled: () => true,
          },
          /* Unshare */
          {
            label: "Remove from Folder",
            icon: Trash2,
            danger: true,
            onClick: () => {
              this.$resources.removeEntity.submit();
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
              return (
                this.selectedEntities.length > 0 &&
                this.selectedEntities.every((x) => x.owner === "Me")
              );
            },
          },
        ].filter((item) => item.isEnabled());
      } else if (this.currentFolder?.write === 1) {
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
                  this.selectedEntities.length === 1 &&
                  !this.selectedEntities[0].is_group &&
                  !this.selectedEntities[0].document
                ) {
                  return (
                    this.selectedEntities[0].allow_download ||
                    this.selectedEntities[0].write ||
                    this.selectedEntities[0].owner === "Me"
                  );
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
          /* TODO: Allow sharing access */
          /*           {
            label: "Share",
            icon: "share-2",
            onClick: () => {
              this.showShareDialog = true;
            },
            isEnabled: () => {
              return this.selectedEntities.length === 1;
            },
          }, */
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
                this.selectedEntities.every((x) => x.owner === "Me" || x.write)
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
              this.pasteEntities(this.selectedEntities[0].name);
            },
            isEnabled: () => {
              return (
                this.$store.state.pasteData.entities.length &&
                this.selectedEntities.length === 1 &&
                this.selectedEntities[0].is_group &&
                (this.selectedEntities[0].write ||
                  this.selectedEntities[0].owner === "Me")
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
                this.selectedEntities[0].is_group
              );
            },
          },
          /*           {
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
          }, */
          {
            label: "Remove from Folder",
            danger: true,
            icon: Trash2,
            onClick: () => {
              this.$resources.removeEntity.submit();
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
      } else {
        return [
          {
            label: "Download",
            icon: FileDown,
            onClick: () => {
              window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
            },
            isEnabled: () => {
              if (
                this.selectedEntities.length === 1 &&
                this.selectedEntities[0].allow_download &&
                !this.selectedEntities[0].is_group &&
                !this.selectedEntities[0].document
              ) {
                return (
                  !this.selectedEntities[0].is_group ||
                  !this.selectedEntities[0].document
                );
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
              if (this.selectedEntities.length === 1) {
                return (
                  this.selectedEntities[0].allow_download &&
                  this.selectedEntities[0].is_group &&
                  !this.selectedEntities[0].document
                );
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
              this.fetchUpdate(this.shareView);
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
  mounted() {
    this.pasteListener = (e) => {
      if (
        (e.ctrlKey || e.metaKey) &&
        (e.key === "v" || e.key === "V") &&
        this.$store.state.pasteData.entities.length &&
        this.$store.state.hasWriteAccess
      )
        this.pasteEntities(this.entityName);
    };
    window.addEventListener("keydown", this.pasteListener);

    this.deleteListener = (e) => {
      if (
        e.key === "Delete" &&
        this.selectedEntities.length &&
        this.selectedEntities.every((x) => x.owner === "Me")
      )
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
    this.emitter.on("fetchFolderContents", () => {
      this.folderContents.fetch();
    });
  },
  unmounted() {
    this.emitter.off("fetchFolderContents");
    window.removeEventListener("keydown", this.pasteListener);
    window.removeEventListener("keydown", this.deleteListener);
    this.$store.commit("setHasWriteAccess", false);
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

    async pasteEntities(newParent = null) {
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
      this.folderContents.fetch();
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
        this.hidePreview();
        this.showEntityContext = false;
        if (this.$store.state.hasWriteAccess) {
          this.showEmptyEntityContextMenu = true;
        }
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
    currentFolder() {
      return {
        url: "drive.api.permissions.get_entity_with_permissions",
        params: { entity_name: this.entityName },
        order_by: this.orderBy,
        // cache: ['pathEntities', this.entityName],
        onSuccess(data) {
          this.currentFolder = data;
          if (data.owner !== this.userId) {
            this.isSharedFolder = true;
            this.$store.commit("setHasWriteAccess", data.write);
          } else {
            this.isSharedFolder = false;
            this.$store.commit("setHasWriteAccess", true);
          }
          let currentBreadcrumbs = this.$store.state.currentBreadcrumbs;
          // Duplicate folder in breadcrumb but unique entity ID
          const index = currentBreadcrumbs.findIndex(
            (item) => item.route === "/folder/" + this.entityName
          );
          if (index !== -1) {
            const slicedBreadCrumb = currentBreadcrumbs.slice(0, index + 1);
            this.$store.commit("setCurrentBreadcrumbs", slicedBreadCrumb);
          } else {
            currentBreadcrumbs.push({
              label: data.title,
              route: `/folder/${this.entityName}`,
            });
          }
          this.$store.commit("setCurrentFolderID", this.entityName);
          this.$store.commit("setCurrentFolder", data);
          this.folderContents.fetch();
        },
        onError(error) {
          if (error && error.exc_type === "PermissionError") {
            this.$store.commit("setError", {
              iconName: "alert-triangle",
              iconClass: "fill-amber-500 stroke-white",
              primaryMessage: "Forbidden",
              secondaryMessage: "Insufficient permissions for this resource",
            });
          }
          this.$router.replace({ name: "Error" });
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
    ownerEntities() {
      return {
        url: "drive.api.files.list_owned_entities",
        // cache: ['folderContents', this.entityName],
        params: {
          entity_name: this.entityName,
          order_by: this.orderBy,
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation,allow_download",
        },
        onSuccess(data) {
          this.folderContents.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? entity.item_count + " items"
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = entity.owner === this.userId ? "Me" : entity.owner;
            this.$store.commit("setCurrentViewEntites", data);
          });
        },
        auto: false,
      };
    },
    sharedEntities() {
      return {
        url: "drive.api.files.list_folder_contents",
        params: {
          entity_name: this.entityName,
          order_by: this.orderBy,
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation,allow_download",
        },
        onSuccess(data) {
          this.folderContents.error = null;
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size;
            entity.file_size = entity.is_group
              ? ""
              : formatSize(entity.file_size);
            entity.modified = formatDate(entity.modified);
            entity.creation = formatDate(entity.creation);
            entity.owner = entity.owner === this.userId ? "Me" : entity.owner;
            this.$store.commit("setCurrentViewEntites", data);
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
        auto: false,
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
          this.folderContents.fetch();
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
        url: "drive.api.files.create_document_entity",
        onSuccess(data) {
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
          this.$store.commit("setEntityInfo", [data]);
          this.previewEntity = data;
          data.owner = "Me";
        },
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },

    removeEntity() {
      return {
        url: "drive.api.files.unshare_entities",
        params: {
          entity_names: JSON.stringify(
            this.selectedEntities.map((entity) => entity.name)
          ),
          move: true,
        },
        onSuccess() {
          this.folderContents.fetch();
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
