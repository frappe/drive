<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white top-0 border-b w-full">
    <div
      class="mx-auto pl-4 py-2.5 pr-1 h-12 z-10 flex items-center justify-between">
      <Breadcrumbs />
      <div class="flex gap-1">
        <div
          v-if="
            $route.meta.documentPage && connectedUsers.length > 1 && isLoggedIn
          "
          class="hidden sm:flex bg-gray-200 rounded justify-center items-center px-1">
          <UsersBar />
        </div>
        <Dropdown
          :options="actionItems"
          placement="right"
          class="basis-5/12 lg:basis-auto">
          <Button
            v-if="$route.meta.documentPage || $route.name === 'File'"
            variant="ghost">
            <FeatherIcon class="h-4" name="more-horizontal" />
          </Button>
        </Dropdown>
        <div v-if="isLoggedIn" class="block sm:flex">
          <Button
            v-if="$route.name === 'Recents'"
            class="line-clamp-1 truncate w-full"
            :disabled="!currentViewEntites?.length"
            theme="red"
            :variant="'subtle'"
            @click="this.emitter.emit('showCTADelete')">
            <template #prefix>
              <FeatherIcon name="trash-2" class="w-4" />
            </template>
            Clear Recents
          </Button>
          <Button
            v-else-if="$route.name === 'Favourites'"
            class="line-clamp-1 truncate"
            :disabled="!currentViewEntites?.length"
            theme="red"
            :variant="'subtle'"
            @click="this.emitter.emit('showCTADelete')">
            <template #prefix>
              <FeatherIcon name="trash-2" class="w-4" />
            </template>
            Clear Favourites
          </Button>
          <Button
            class="line-clamp-1 truncate"
            v-else-if="$route.name === 'Trash'"
            @click="this.emitter.emit('showCTADelete')"
            :disabled="!currentViewEntites?.length"
            theme="red"
            :variant="'subtle'">
            <template #prefix>
              <FeatherIcon name="trash-2" class="w-4" />
            </template>
            Empty Trash
          </Button>
          <Button
            v-else-if="$route.name === 'Document'"
            :disabled="!$store.state.hasWriteAccess"
            @click="emitter.emit('saveDocument')"
            class="bg-gray-200 rounded flex justify-center items-center px-1"
            variant="subtle">
            <template #prefix>
              <FeatherIcon name="save" class="w-4" />
            </template>
            Save
          </Button>
          <Dropdown
            v-else
            :options="newEntityOptions"
            placement="left"
            class="basis-5/12 lg:basis-auto">
            <Button variant="solid">
              <template #prefix>
                <FeatherIcon name="upload" class="w-4" />
              </template>
              New
              <template #suffix>
                <FeatherIcon name="chevron-down" class="w-4" />
              </template>
            </Button>
          </Dropdown>
          <div v-if="$store.state.hasWriteAccess"></div>
          <!--

          Pushed implementation
          
        <Button
          class="stroke-1.5 ml-4 md:ml-5"
          appearance="minimal"
          icon="bell"></Button>
          
        --></div>
        <div v-if="!isLoggedIn" class="ml-auto">
          <Button @click="$router.push({ name: 'Login' })" variant="solid">
            Sign In
          </Button>
        </div>
      </div>
    </div>
  </nav>
  <NewFolderDialog
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
    :parent="$route.params.entityName"
    :entity="selectedEntities[0]"
    @success="
      () => {
        showRenameDialog = false;
      }
    " />
</template>
<script>
import UsersBar from "./UsersBar.vue";
import { Dropdown, FeatherIcon, Button } from "frappe-ui";
import NewFolderDialog from "@/components/NewFolderDialog.vue";
import RenameDialog from "@/components/RenameDialog.vue";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import { formatDate } from "@/utils/format";
import { getLink } from "@/utils/getLink";
import {
  folderDownload,
  selectedEntitiesDownload,
} from "@/utils/folderDownload";
import {
  FileDown,
  FolderDown,
  TextCursorInput,
  Link2,
  Star,
  FolderPlus,
  FolderUp,
  FileUp,
  FileText,
} from "lucide-vue-next";
import { h } from "vue";

export default {
  name: "Navbar",
  components: {
    RenameDialog,
    NewFolderDialog,
    Dropdown,
    FeatherIcon,
    Button,
    Breadcrumbs,
    UsersBar,
    FileUp,
    FileDown,
    FolderUp,
    FolderPlus,
    FileText,
  },
  props: {
    breadcrumbs: {
      type: Array,
      default: null,
    },
    mobileSidebarIsOpen: {
      type: Boolean,
      required: true,
    },
  },
  emits: ["toggleMobileSidebar", "fetchRecents"],
  data() {
    return {
      previewEntity: null,
      showPreview: false,
      showNewFolderDialog: false,
      showRenameDialog: false,
      newEntityOptions: [
        {
          group: "Upload",
          items: [
            {
              label: "Upload File",
              icon: h(FileUp, {
                id: "foo",
                class: "text-gray-900 stroke-[1.5]",
              }),
              onClick: () => this.emitter.emit("uploadFile"),
            },
            {
              label: "Upload Folder",
              icon: h(FolderUp, {
                id: "foo",
                class: "text-gray-900 stroke-[1.5]",
              }),
              onClick: () => this.emitter.emit("uploadFolder"),
              isEnabled: () => this.selectedEntities.length === 0,
            },
          ],
        },
        {
          group: "New",
          items: [
            {
              label: "New Folder",
              icon: h(FolderPlus, {
                id: "foo",
                class: "text-gray-900 stroke-[1.5]",
              }),
              onClick: () => (this.showNewFolderDialog = true),
            },
            {
              label: "New Document",
              icon: h(FileText, {
                id: "foo",
                class: "text-gray-900 stroke-[1.5]",
              }),
              onClick: async () => {
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

              isEnabled: () => this.selectedEntities?.length === 0,
            },
          ],
        },
      ],
    };
  },
  computed: {
    selectedEntities() {
      return this.$store.state.entityInfo;
    },
    actionItems() {
      return [
        {
          label: "Download",
          icon: FileDown,
          onClick: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`;
          },
          isEnabled: () => {
            if (this.selectedEntities?.length === 1) {
              if (
                this.selectedEntities?.length === 1 &&
                !this.selectedEntities[0]?.is_group &&
                !this.selectedEntities[0]?.document
              ) {
                return (
                  this.selectedEntities[0]?.allow_download ||
                  this.selectedEntities[0]?.owner === "Me"
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
              this.selectedEntities?.length === 1 &&
              !this.selectedEntities[0]?.is_group
            ) {
              return false;
            }
            if (this.selectedEntities?.length) {
              const allEntitiesSatisfyCondition = this.selectedEntities?.every(
                (entity) => {
                  return entity.allow_download || entity.owner === "Me";
                }
              );
              return allEntitiesSatisfyCondition;
            }
          },
        },
        {
          label: "Get Link",
          icon: Link2,
          onClick: () => {
            getLink(this.selectedEntities[0]);
          },
          isEnabled: () => {
            return this.selectedEntities?.length === 1;
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
              this.selectedEntities?.length === 1 &&
              (this.selectedEntities[0]?.write ||
                this.selectedEntities[0]?.owner === "Me")
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
              this.selectedEntities?.length > 0 &&
              this.isLoggedIn &&
              this.selectedEntities?.every((x) => !x.is_favourite)
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
              this.selectedEntities?.length > 0 &&
              this.selectedEntities?.every((x) => x.is_favourite)
            );
          },
        },
      ].filter((item) => item.isEnabled());
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    imageURL() {
      return this.$store.state.user.imageURL;
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    connectedUsers() {
      return this.$store.state.connectedUsers;
    },
    currentViewEntites() {
      return this.$store.state.currentViewEntites;
    },
  },
  /*   methods: {
    openEntity(entity) {
      if (entity.is_group) {
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
        this.previewEntity = entity;
        this.showPreview = true;
      }
    },
    hidePreview() {
      this.showPreview = false;
      this.previewEntity = null;
    },
  }, */
  resources: {
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
          this.$store.state.entityInfo[0].is_favourite =
            !this.$store.state.entityInfo[0].is_favourite;
        },
      };
    },
  },
};
</script>
