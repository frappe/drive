<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white top-0 border-b w-full">
    <div
      class="mx-auto pl-4 py-2.5 pr-2 h-12 z-10 flex items-center justify-between">
      <Breadcrumbs v-if="isLoggedIn" />
      <!--       
  <div class="flex items-center">
        <router-link to="/" class="hidden md:block"></router-link>
        <div class="flex items-center md:hidden">
          <button
            class="mr-5 inline-flex items-center justify-center text-gray-700 rounded-md focus:outline-none focus:shadow-outline-gray"
            @click="$emit('toggleMobileSidebar')">
            <FeatherIcon
              v-if="!mobileSidebarIsOpen"
              name="menu"
              class="w-6 h-6" />
            <FeatherIcon v-else name="x" class="w-6 h-6" />
          </button>
        </div>
      </div> 
       $store.state.hasWriteAccess -->
      <div v-if="isLoggedIn" class="flex items-center">
        <Dropdown
          :options="fileOptions"
          placement="left"
          class="basis-5/12 lg:basis-auto">
          <Button v-if="$route.meta.documentPage && isLoggedIn" variant="ghost">
            <FeatherIcon class="h-4" name="more-horizontal" />
          </Button>
        </Dropdown>
        <div
          v-if="
            $route.meta.documentPage && connectedUsers.length > 1 && isLoggedIn
          "
          class="bg-gray-200 rounded flex justify-center items-center px-1 mx-2">
          <UsersBar />
        </div>
        <Button
          v-if="$route.name === 'Recent'"
          class="bg-red-100 text-red-700"
          variant="minimal"
          @click="$resources.clearRecent.submit()">
          <template #prefix>
            <FeatherIcon name="trash-2" class="w-4" />
          </template>
          Clear Recents
        </Button>
        <Button
          v-else-if="$route.name === 'Favourites'"
          class="bg-red-100 text-red-700"
          variant="minimal"
          @click="$resources.clearFavourites.submit()">
          <template #prefix>
            <FeatherIcon name="trash-2" class="w-4" />
          </template>
          Clear Favourites
        </Button>
        <Button
          v-else-if="$route.name === 'Trash'"
          @click="emitter.emit('clearTrashed')"
          class="bg-red-100 text-red-700"
          variant="minimal">
          <template #prefix>
            <FeatherIcon name="trash-2" class="w-4" />
          </template>
          Empty Trash
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
          
        -->
      </div>
      <div v-else class="ml-auto">
        <Button @click="$router.push({ name: 'Login' })" variant="solid">
          Sign In
        </Button>
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
</template>
<script>
import UsersBar from "./UsersBar.vue";
import { Dropdown, FeatherIcon, Button } from "frappe-ui";
import NewFolderDialog from "@/components/NewFolderDialog.vue";
import Breadcrumbs from "@/components/Breadcrumbs.vue";
import { formatDate } from "@/utils/format";
import { FileDown } from "lucide-vue-next";
import { FileUp, FolderUp, FolderPlus, FileText } from "lucide-vue-next";
import { h } from "vue";

export default {
  name: "Navbar",
  components: {
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
      newEntityOptions: [
        {
          group: "Upload",
          items: [
            {
              label: "Upload file",
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
              label: "New folder",
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

              isEnabled: () => this.selectedEntities.length === 0,
            },
          ],
        },
      ],
      fileOptions: [
        {
          icon: FileDown,
          label: "Export to PDF",
          onClick: () => this.emitter.emit("exportDocToPDF"),
        },
        {
          icon: FileDown,
          label: "Import from Word",
          onClick: () => this.emitter.emit("importDocFromWord"),
        },
      ],
      showSearchPopup: false,
    };
  },
  computed: {
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
    clearRecent() {
      return {
        url: "drive.api.files.remove_recents",
        params: {
          clear_all: true,
        },
        onSuccess() {
          this.emitter.emit("fetchRecents");
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
    clearFavourites() {
      return {
        url: "drive.api.files.add_or_remove_favourites",
        params: {
          clear_all: true,
        },
        onSuccess() {
          this.emitter.emit("fetchFavourites");
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
