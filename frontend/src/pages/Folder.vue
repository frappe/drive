<template>
  <div class="h-full" @contextmenu="toggleEmptyContext">
    <FolderContentsError
      v-if="$resources.folderContents.error"
      :error="$resources.folderContents.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folderContents="$resources.folderContents.data"
      :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @showEntityContext="(event) => toggleEntityContext(event)"
      @showEmptyEntityContext="(event) => toggleEmptyContext(event)"
      @closeContextMenuEvent="closeContextMenu"
      @fetchFolderContents="() => $resources.folderContents.fetch()">
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :columnHeaders="columnHeaders"
          :showInfoButton="showInfoButton" />
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
      @showEmptyEntityContext="(event) => toggleEmptyContext(event)"
      @closeContextMenuEvent="closeContextMenu"
      @fetchFolderContents="() => $resources.folderContents.fetch()">
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :columnHeaders="columnHeaders"
          :showInfoButton="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection />
      </template>
    </ListView>

    <FilePreview
      v-if="showPreview"
      @hide="hidePreview"
      :previewEntity="previewEntity" />
    <EntityContextMenu
      v-if="showEntityContext"
      :actionItems="actionItems"
      :entityContext="entityContext"
      :close="closeContextMenu"
      v-on-outside-click="closeContextMenu" />
    <EmptyEntityContextMenu
      v-if="showEmptyEntityContextMenu"
      :actionItems="emptyActionItems"
      :entityContext="entityContext"
      :close="closeContextMenu"
      v-on-outside-click="closeContextMenu" />
    <NewFolderDialog
      v-model="showNewFolderDialog"
      :parent="$route.params.entityName"
      @success="
        () => {
          this.emitter.emit('fetchFolderContents');
          showNewFolderDialog = false;
        }
      " />
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
      :entityName="shareName"
      @success="$resources.folderContents.fetch()" />
    <div class="hidden" id="dropzoneElement" />
  </div>
</template>

<script>
import Dropzone from "dropzone";
import ListView from "@/components/ListView.vue";
import GridView from "@/components/GridView.vue";
import DriveToolBar from "@/components/DriveToolBar.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import FilePreview from "@/components/FilePreview.vue";
import NewFolderDialog from "@/components/NewFolderDialog.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import ShareDialog from "@/components/ShareDialog.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";

export default {
  name: "Home",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    FilePreview,
    NewFolderDialog,
    RenameDialog,
    ShareDialog,
    GeneralDialog,
    FolderContentsError,
    EntityContextMenu,
    EmptyEntityContextMenu,
  },
  props: {
    entityName: {
      type: String,
      required: false,
      default: "",
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
    showEmptyEntityContextMenu: false,
    showNewFolderDialog: false,

    entityContext: {},
    breadcrumbs: [{ label: "Home", route: "/" }],
    isSharedFolder: false,
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
    emptyActionItems() {
      return [
        {
          label: "Upload File",
          icon: "file",
          handler: () => this.emitter.emit("uploadFile"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "Upload Folder",
          icon: "folder",
          handler: () => this.emitter.emit("uploadFolder"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New Folder",
          icon: "folder-plus",
          handler: () => (this.showNewFolderDialog = true),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "Paste",
          icon: "clipboard",
          handler: async () => {
            for (let i = 0; i < this.$store.state.cutEntities.length; i++) {
              await this.$resources.moveEntity.submit({
                method: "move",
                entity_name: this.$store.state.cutEntities[i],
                new_parent: this.entityName,
              });
            }
            this.selectedEntities = [];
            this.$store.commit("setCutEntities", []);
            this.$resources.folderContents.fetch();
          },
          isEnabled: () =>
            this.$store.state.cutEntities.length > 0 &&
            this.$store.state.hasWriteAccess,
        },
      ].filter((item) => item.isEnabled());
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
                this.selectedEntities[0].write ||
                this.selectedEntities[0].owner === "me")
            );
          },
        },
        {
          label: "Share",
          icon: "share-2",
          handler: () => {
            this.showShareDialog = true;
          },
          isEnabled: () => {
            return (
              (this.selectedEntities.length === 1 ||
                (this.entityName && !this.selectedEntities.length)) &&
              !this.isSharedFolder
            );
          },
        },
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
              (this.selectedEntities[0].write ||
                this.selectedEntities[0].owner === "me")
            );
          },
        },
        {
          label: "Cut",
          icon: "scissors",
          handler: () => {
            this.$store.commit(
              "setCutEntities",
              this.selectedEntities.map((x) => x.name)
            );
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner === "me")
            );
          },
        },
        {
          label: "Paste into Folder",
          icon: "clipboard",
          handler: async () => {
            for (let i = 0; i < this.$store.state.cutEntities.length; i++) {
              await this.$resources.moveEntity.submit({
                method: "move",
                entity_name: this.$store.state.cutEntities[i],
                new_parent: this.selectedEntities[0].name,
              });
            }
            this.selectedEntities = [];
            this.$store.commit("setCutEntities", []);
            this.$resources.folderContents.fetch();
          },
          isEnabled: () => {
            return (
              this.$store.state.cutEntities.length > 0 &&
              this.selectedEntities.length === 1 &&
              (this.selectedEntities[0].write ||
                this.selectedEntities[0].owner === "me")
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
          label: "Change Color",
          icon: "droplet",
          isEnabled: () => {
            return (
              this.selectedEntities.length === 1 &&
              this.selectedEntities[0].is_group
            );
          },
        },
        {
          label: "Remove",
          icon: "trash-2",
          handler: () => {
            this.$resources.removeEntity.submit();
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length > 0 &&
              this.selectedEntities.every((x) => x.owner != "me") &&
              (this.selectedEntities.every((x) => x.write) ||
                !this.isSharedFolder)
            );
          },
        },
        {
          label: "Move to Trash",
          icon: "trash-2",
          handler: () => {
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
    initializeDropzone() {
      let componentContext = this;
      this.dropzone = new Dropzone(this.$el.parentNode, {
        paramName: "file",
        parallelUploads: 1,
        autoProcessQueue: true,
        uploadMultiple: false,
        clickable: "#dropzoneElement",
        previewsContainer: "#dropzoneElement",
        chunking: true,
        forceChunking: true,
        url: "/api/method/drive.api.files.upload_file",
        maxFilesize: 10 * 1024, // 10GB
        chunkSize: 5 * 1024 * 1024, // 5MB
        headers: {
          "X-Frappe-CSRF-Token": window.csrf_token,
          Accept: "application/json",
        },
        sending: function (file, xhr, formData, chunk) {
          file.parent ? formData.append("parent", file.parent) : null;
          file.webkitRelativePath
            ? formData.append(
                "fullpath",
                file.webkitRelativePath.slice(
                  0,
                  file.webkitRelativePath.indexOf("/")
                )
              )
            : null;
          // WARNING: dropzone hidden input element click does not append fullPath to formdata thats why webkitRelativePath was used
          file.fullPath
            ? formData.append(
                "fullpath",
                file.fullPath.slice(0, file.fullPath.indexOf("/"))
              )
            : null;
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
      this.dropzone.on("addedfile", function (file) {
        file.parent = componentContext.entityName;
        componentContext.$store.commit("pushToUploads", {
          uuid: file.upload.uuid,
          name: file.name,
          progress: 0,
        });
      });
      this.dropzone.on("uploadprogress", function (file, progress) {
        componentContext.$store.commit("updateUpload", {
          uuid: file.upload.uuid,
          progress: progress,
        });
      });
      this.dropzone.on("error", function (file, message, xhr) {
        let error_message;
        if (message._server_messages) {
          error_message = JSON.parse(message._server_messages)
            .map((element) => JSON.parse(element).message)
            .join("\n");
        }
        error_message = error_message || "Upload failed";
        componentContext.$store.commit("updateUpload", {
          uuid: file.upload.uuid,
          error: error_message,
        });
      });
      this.dropzone.on("complete", function (file) {
        componentContext.$resources.folderContents.fetch();
        componentContext.$store.commit("updateUpload", {
          uuid: file.upload.uuid,
          completed: true,
        });
      });
      this.emitter.on("uploadFile", () => {
        if (componentContext.dropzone.hiddenFileInput)
          componentContext.dropzone.hiddenFileInput.click();
      });
      this.emitter.on("uploadFolder", () => {
        if (componentContext.dropzone.hiddenFileInput) {
          componentContext.dropzone.hiddenFileInput.setAttribute(
            "webkitdirectory",
            true
          );
          componentContext.dropzone.hiddenFileInput.click();
        }
      });
    },

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
        this.showEmptyEntityContextMenu = true;
        this.entityContext = event;
      }
    },
    closeContextMenu() {
      this.showEntityContext = false;
      this.showEmptyEntityContextMenu = false;
      this.entityContext = undefined;
    },
  },
  watch: {
    async entityName() {
      await this.$resources.folderAccess.fetch();
      this.$store.commit(
        "setHasWriteAccess",
        !!this.$resources.folderAccess.data?.write
      );
      this.selectedEntities = [];
      if (!this.dropzone && this.$store.state.hasWriteAccess)
        this.initializeDropzone();
    },
  },

  async mounted() {
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

    await this.$resources.folderAccess.fetch();
    this.$store.commit(
      "setHasWriteAccess",
      !!this.$resources.folderAccess.data?.write
    );
    let componentContext = this;
    this.emitter.on("fetchFolderContents", () => {
      componentContext.$resources.folderContents.fetch();
    });
    if (this.$store.state.hasWriteAccess) this.initializeDropzone();
  },

  unmounted() {
    this.$store.commit("setHasWriteAccess", false);
    if (this.dropzone) this.dropzone.destroy();
  },

  resources: {
    folderAccess() {
      return {
        url: "drive.api.permissions.get_user_access",
        params: { entity_name: this.entityName },
      };
    },
    createFolder() {
      return {
        url: "drive.api.files.create_folder",
        params: {
          title: this.folderName,
          parent: this.parent,
        },
        validate(params) {
          if (!params?.title) {
            return "Folder name is required";
          }
        },
        onSuccess(data) {
          this.$resources.folderContents.fetch();
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
      };
    },

    moveEntity() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        params: {
          method: "move",
          entity_name: "entity name",
          new_parent: "new entity parent",
        },
        validate(params) {
          if (!params?.new_parent) {
            return "New parent is required";
          }
        },
      };
    },

    folderContents() {
      return {
        url: "drive.api.files.list_folder_contents",
        // cache: ['folderContents', this.entityName],
        params: {
          entity_name: this.entityName,
          order_by: this.orderBy,
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation,allow_download",
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

    pathEntities() {
      return {
        url: "drive.api.files.get_entities_in_path",
        // cache: ['pathEntities', this.entityName],
        params: {
          entity_name: this.entityName,
        },
        onSuccess(data) {
          this.isSharedFolder = data.is_shared;
          let breadcrumbs = [];
          if (this.isSharedFolder)
            breadcrumbs.push({
              label: "Shared With Me",
              route: "/shared",
            });
          data.entities.forEach((entity, index) => {
            if (index === 0) {
              const isHome = entity.owner === this.userId;
              breadcrumbs.push({
                label: isHome ? "Home" : entity.title,
                route: isHome ? "/" : `/folder/${entity.name}`,
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
              label: "...",
              route: "",
            });
          }
          this.breadcrumbs = breadcrumbs;
        },
        auto: Boolean(this.entityName),
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
          this.$resources.folderContents.fetch();
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
