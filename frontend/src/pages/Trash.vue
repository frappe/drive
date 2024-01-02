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
      @show-entity-context="(event) => toggleEntityContext(event)"
      @close-context-menu-event="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders"
          :action-loading="actionLoading"
          :show-upload-button="false" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="'Trash is currently empty'"
          :secondary-message="'Items in the trash will be deleted automatically after 30 days'" />
      </template>
    </GridView>

    <ListView
      v-else
      :folder-contents="$resources.folderContents.data"
      :selected-entities="selectedEntities"
      @entity-selected="(selected) => (selectedEntities = selected)"
      @show-entity-context="(event) => toggleEntityContext(event)"
      @close-context-menu-event="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :action-items="actionItems"
          :column-headers="columnHeaders"
          :action-loading="actionLoading"
          :show-upload-button="false" />
      </template>
      <template #placeholder>
        <NoFilesSection
          :primary-message="'Trash is currently empty'"
          :secondary-message="'Items in the trash will be deleted automatically after 30 days'" />
      </template>
    </ListView>
    <EntityContextMenu
      v-if="showEntityContext"
      v-on-outside-click="closeContextMenu"
      :action-items="actionItems"
      :entity-context="entityContext"
      :close="closeContextMenu" />
    <DeleteDialog
      v-model="showDeleteDialog"
      :entities="
        selectedEntities.length > 0
          ? selectedEntities
          : $resources.folderContents.data
      "
      @success="
        () => {
          $resources.folderContents.fetch();
          showDeleteDialog = false;
          selectedEntities = [];
        }
      " />
    <GeneralDialog
      v-model="showRestoreDialog"
      :entities="selectedEntities"
      :for="'restore'"
      @success="
        () => {
          $resources.folderContents.fetch();
          showRestoreDialog = false;
          selectedEntities = [];
        }
      " />
    <div />
  </div>
</template>

<script>
import DriveToolBar from "@/components/DriveToolBar.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import GridView from "@/components/GridView.vue";
import ListView from "@/components/ListView.vue";
import DeleteDialog from "@/components/DeleteDialog.vue";
import GeneralDialog from "@/components/GeneralDialog.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatDate, formatSize } from "@/utils/format";
import { RotateCcw, Trash2 } from "lucide-vue-next";

export default {
  name: "Trash",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    DeleteDialog,
    GeneralDialog,
    NoFilesSection,
    FolderContentsError,
    EntityContextMenu,
    RotateCcw,
    Trash2,
  },
  data: () => ({
    selectedEntities: [],
    breadcrumbs: [{ label: "Trash", route: "/trash" }],
    actionLoading: false,
    showDeleteDialog: false,
    showRestoreDialog: false,
    showEntityContext: false,
    entityContext: {},
  }),
  computed: {
    userId() {
      return this.$store.state.auth.user_id;
    },
    orderBy() {
      return this.$store.state.sortOrder.ascending
        ? this.$store.state.sortOrder.field
        : `${this.$store.state.sortOrder.field} desc`;
    },
    actionItems() {
      return [
        {
          label: "Empty Trash",
          icon: Trash2,
          onClick: () => {
            this.showDeleteDialog = true;
          },
          isEnabled: () => {
            return (
              this.selectedEntities.length === 0 &&
              this.$resources.folderContents.data?.length > 0
            );
          },
        },
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
        {
          label: "Type",
          field: "mime_type",
          sortable: true,
        },
      ].filter((item) => item.sortable);
    },
  },

  mounted() {
    this.emitter.on("clearTrashed", () => {
      this.clearTrashed();
      this.showDeleteDialog = true;
    });
    this.$store.commit("setCurrentBreadcrumbs", this.breadcrumbs);
    this.deleteListener = (e) => {
      if (e.key === "Delete" && this.selectedEntities.length)
        this.showDeleteDialog = true;
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
  },
  unmounted() {
    window.removeEventListener("keydown", this.deleteListener);
  },
  methods: {
    clearTrashed() {
      this.selectedEntities = this.$resources.folderContents.data;
    },
    toggleEntityContext(event) {
      if (!event) this.showEntityContext = false;
      else {
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
        url: "drive.api.files.get_trashed_entities",
        params: {
          order_by: this.orderBy,
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation",
          is_active: 0,
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
