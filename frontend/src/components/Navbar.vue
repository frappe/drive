<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white z-10 sticky top-0"
    :class="{ 'shadow-sm': $route.meta.documentPage }">
    <div class="mx-auto py-2 px-5 h-16 md:h-12 z-10 flex justify-between">
      <Breadcrumbs
        :breadcrumb-links="currentBreadcrumbs"
        class="hidden md:block" />
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
        <!--         <Button
          v-if="$route.meta.documentPage && isLoggedIn"
          icon-left="chevron-left"
          @click="$router.go(-1)">
          Back to Files
        </Button> -->
      </div>
      <div
        v-if="!$route.meta.documentPage"
        class="relative ml-auto mt-2.5 md:mt-0.5 z-10">
        <SearchPopup
          v-if="isLoggedIn"
          @open-entity="(entity) => openEntity(entity)" />
      </div>
      <div v-if="isLoggedIn" class="flex items-center">
        <Dropdown
          :options="$store.state.hasWriteAccess ? addOptions : []"
          placement="left"
          class="basis-5/12 lg:basis-auto">
          <Button
            v-if="$store.state.hasWriteAccess"
            id="upload-button"
            class="ml-4 md:ml-8 mr-5 h-8 w-8 rounded-full"
            appearance="primary"
            icon="plus"></Button>
        </Dropdown>
        <div v-if="$store.state.hasWriteAccess" class="border h-5"></div>
        <!--

          Pushed implementation
          
        <Button
          class="stroke-1.5 ml-4 md:ml-5"
          appearance="minimal"
          icon="bell"></Button>
          
        -->
        <div class="relative ml-3">
          <Dropdown :options="accountOptions" placement="right">
            <button
              id="user-menu"
              class="flex items-center max-w-xs text-sm text-white rounded-full focus:outline-none focus:shadow-solid"
              aria-label="User menu"
              aria-haspopup="true">
              <div class="flex items-center gap-4">
                <!-- eslint-disable-next-line vue/attribute-hyphenation -->
                <Avatar :label="fullName" :imageURL="imageURL" />
              </div>
            </button>
          </Dropdown>
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
  <FilePreview
    v-if="showPreview"
    :preview-entity="previewEntity"
    @hide="hidePreview" />
</template>
<script>
import { Avatar, Dropdown, FeatherIcon, Button } from "frappe-ui";
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue";
import SearchPopup from "@/components/SearchPopup.vue";
import NewFolderDialog from "@/components/NewFolderDialog.vue";
import FilePreview from "@/components/FilePreview.vue";
import Breadcrumbs from "@/components/Breadcrumbs.vue";

export default {
  name: "Navbar",
  components: {
    FilePreview,
    FrappeDriveLogo,
    SearchPopup,
    NewFolderDialog,
    Avatar,
    Dropdown,
    FeatherIcon,
    Button,
    Breadcrumbs,
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
  emits: ["toggleMobileSidebar"],
  data() {
    return {
      previewEntity: null,
      showPreview: false,
      showNewFolderDialog: false,
      addOptions: [
        {
          label: "Upload file",
          icon: "upload",
          handler: () => this.emitter.emit("uploadFile"),
        },
        {
          label: "Upload Folder",
          icon: "folder",
          handler: () => this.emitter.emit("uploadFolder"),
          isEnabled: () => this.selectedEntities.length === 0,
        },
        {
          label: "New folder",
          icon: "folder-plus",
          handler: () => (this.showNewFolderDialog = true),
        },
        {
          label: "New Document",
          icon: "file-text",
          handler: async () => {
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
      accountOptions: [
        {
          label: this.$store.state.user.fullName,
        },
        {
          label: "Log out",
          handler: () => this.$store.dispatch("logout"),
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
    currentBreadcrumbs() {
      return this.$store.state.currentBreadcrumbs;
    },
  },
  methods: {
    openEntity(entity) {
      if (entity.is_group) {
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
  },
  resources: {
    createDocument() {
      return {
        url: "drive.api.files.create_document_entity",
        onSuccess(data) {
          this.previewEntity = data;
        },
        onError(data) {
          console.log(data);
        },
        auto: false,
      };
    },
  },
};
</script>
<style>
#upload-button {
  border-radius: 100%;
}
</style>
