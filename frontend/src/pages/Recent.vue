<template>
  <div class="h-full">
    <FolderContentsError
      v-if="$resources.recentDriveEntity.error"
      :error="$resources.recentDriveEntity.error" />

    <GridView
      v-else-if="$store.state.view === 'grid'"
      :folderContents="entities.sort((a, b) => b.accessed - a.accessed)"
      :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @showEntityContext="(event) => toggleEntityContext(event)"
      @closeContextMenuEvent="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :showInfoButton="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection
          secondaryMessage="You have not viewed any files recently" />
      </template>
    </GridView>

    <ListView
      v-else
      :folderContents="entities.sort((a, b) => b.accessed - a.accessed)"
      :selectedEntities="selectedEntities"
      @entitySelected="(selected) => (selectedEntities = selected)"
      @openEntity="(entity) => openEntity(entity)"
      @showEntityContext="(event) => toggleEntityContext(event)"
      @closeContextMenuEvent="closeContextMenu">
      <template #toolbar>
        <DriveToolBar
          :actionItems="actionItems"
          :breadcrumbs="breadcrumbs"
          :showInfoButton="showInfoButton" />
      </template>
      <template #placeholder>
        <NoFilesSection
          secondaryMessage="You have not viewed any file recently" />
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
  </div>
</template>

<script>
import ListView from "@/components/ListView.vue";
import GridView from "@/components/GridView.vue";
import DriveToolBar from "@/components/DriveToolBar.vue";
import NoFilesSection from "@/components/NoFilesSection.vue";
import FilePreview from "@/components/FilePreview.vue";
import FolderContentsError from "@/components/FolderContentsError.vue";
import EntityContextMenu from "@/components/EntityContextMenu.vue";
import { formatSize, formatDate } from "@/utils/format";
import { entries, get } from "idb-keyval";

export default {
  name: "Recent",
  components: {
    ListView,
    GridView,
    DriveToolBar,
    NoFilesSection,
    FilePreview,
    FolderContentsError,
    EntityContextMenu,
  },
  data: () => ({
    previewEntity: null,
    showPreview: false,
    showEntityContext: false,
    entityContext: {},
    entities: [],
    selectedEntities: [],
    breadcrumbs: [{ label: "Recents", route: "/recent" }],
  }),

  computed: {
    showInfoButton() {
      return !!this.selectedEntities.length && !this.$store.state.showInfo;
    },
    actionItems() {
      return [
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
      ].filter((item) => item.isEnabled());
    },
  },
  mounted() {
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
    entries().then((result) =>
      result.forEach((entityEntries) => {
        this.$resources.recentDriveEntity.fetch({
          entity_name: entityEntries[0],
          fields:
            "name, title, is_group, owner, modified, file_size, mime_type, creation",
        });
      })
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
    recentDriveEntity() {
      return {
        method: "GET",
        url: "drive.api.files.get_entity",
        params: {
          entity_name: "entity_name",
          fields:
            "name,title,is_group,owner,modified,file_size,mime_type,creation",
        },
        onSuccess(data) {
          data.size_in_bytes = data.file_size;
          data.file_size = data.is_group ? "-" : formatSize(data.file_size);
          data.modified = formatDate(data.modified);
          get(data.name).then((val) => (data.accessed = val));
          data.creation = formatDate(data.creation);
          this.entities.push(data);
        },
        onError(error) {
          console.log(error);
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
