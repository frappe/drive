<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white top-0 border-b min-w-full"
  >
    <div
      class="mx-auto pl-4 py-2.5 pr-2 h-12 z-10 flex items-center justify-between"
    >
      <Breadcrumbs />
      <div class="flex gap-1">
        <div
          v-if="
            $route.meta.documentPage && connectedUsers.length > 1 && isLoggedIn
          "
          class="hidden sm:flex bg-gray-200 rounded justify-center items-center px-1"
        >
          <UsersBar />
        </div>
        <Dropdown
          v-if="$store.state.entityInfo"
          :options="actionItems"
          placement="right"
          class="basis-5/12 lg:basis-auto"
        >
          <Button
            v-if="
              $route.meta.documentPage ||
              $route.name === 'File' ||
              $route.name === 'Folder'
            "
            variant="ghost"
            @click="handleSelectedEntity"
          >
            <FeatherIcon class="h-4" name="more-horizontal" />
          </Button>
        </Dropdown>
        <div v-if="isLoggedIn" class="block sm:flex">
          <Button
            v-if="$route.name === 'Document' || $route.name === 'File'"
            :variant="'solid'"
            :disabled="$store.state.entityInfo[0]?.owner !== 'You'"
            class="bg-gray-200 rounded flex justify-center items-center px-1"
            @click="emitter.emit('showShareDialog')"
          >
            <template #prefix>
              <Share class="w-4" />
            </template>
            Share
          </Button>
          <Button
            v-else-if="$route.name === 'Recents'"
            class="line-clamp-1 truncate w-full"
            :disabled="!currentViewEntites?.length"
            theme="red"
            :variant="'subtle'"
            @click="emitter.emit('showCTADelete')"
          >
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
            @click="emitter.emit('showCTADelete')"
          >
            <template #prefix>
              <FeatherIcon name="trash-2" class="w-4" />
            </template>
            Clear Favourites
          </Button>
          <Button
            v-else-if="$route.name === 'Trash'"
            class="line-clamp-1 truncate"
            :disabled="!currentViewEntites?.length"
            theme="red"
            :variant="'subtle'"
            @click="emitter.emit('showCTADelete')"
          >
            <template #prefix>
              <FeatherIcon name="trash-2" class="w-4" />
            </template>
            Empty Trash
          </Button>
          <Dropdown
            v-else
            :options="newEntityOptions"
            placement="left"
            class="basis-5/12 lg:basis-auto"
          >
            <Button variant="solid" :disabled="canUpload">
              <template #prefix>
                <FeatherIcon name="upload" class="w-4" />
              </template>
              Upload
              <template #suffix>
                <FeatherIcon name="chevron-down" class="w-4" />
              </template>
            </Button>
          </Dropdown>
        </div>
        <div v-if="!isLoggedIn" class="ml-auto">
          <Button variant="solid" @click="$router.push({ name: 'Login' })">
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
        emitter.emit('fetchFolderContents')
        showNewFolderDialog = false
      }
    "
  />
  <RenameDialog
    v-if="showRenameDialog"
    v-model="showRenameDialog"
    :parent="$route.params.entityName"
    :entity="selectedEntities[0] ? selectedEntities[0] : currentFolder[0]"
    @success="
      () => {
        showRenameDialog = false
      }
    "
  />
</template>
<script>
import UsersBar from "./UsersBar.vue"
import { Dropdown, FeatherIcon, Button } from "frappe-ui"
import NewFolderDialog from "@/components/NewFolderDialog.vue"
import RenameDialog from "@/components/RenameDialog.vue"
import Breadcrumbs from "@/components/Breadcrumbs.vue"
import { formatDate } from "@/utils/format"
import { getLink } from "@/utils/getLink"
import {
  folderDownload,
  selectedEntitiesDownload,
} from "@/utils/folderDownload"
import Share from "./EspressoIcons/Share.vue"
import Star from "./EspressoIcons/Star.vue"
import Rename from "./EspressoIcons/Rename.vue"
import Link from "./EspressoIcons/Link.vue"
import Download from "./EspressoIcons/Download.vue"
import NewFolder from "./EspressoIcons/NewFolder.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import NewFile from "./EspressoIcons/NewFile.vue"

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
    Share,
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
              icon: FileUpload,
              onClick: () => this.emitter.emit("uploadFile"),
            },
            {
              label: "Upload Folder",
              icon: FolderUpload,
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
              icon: NewFolder,
              onClick: () => (this.showNewFolderDialog = true),
            },
            {
              label: "New Document",
              icon: NewFile,
              onClick: async () => {
                await this.$resources.createDocument.submit({
                  title: "Untitled Document",
                  content: null,
                  parent: this.$store.state.currentFolderID,
                })
                this.$router.push({
                  name: "Document",
                  params: { entityName: this.previewEntity.name },
                })
              },

              isEnabled: () => this.selectedEntities?.length === 0,
            },
          ],
        },
      ],
    }
  },
  computed: {
    selectedEntities() {
      if (this.$route.name === "Folder") {
        return this.$store.state.currentFolder
      }
      return this.$store.state.entityInfo
    },
    actionItems() {
      return [
        {
          label: "Download",
          icon: Download,
          onClick: () => {
            window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.selectedEntities[0].name}&trigger_download=1`
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
                  this.selectedEntities[0]?.owner === "You"
                )
              }
            }
          },
        },
        {
          label: "Download",
          icon: Download,
          onClick: () => {
            if (this.selectedEntities.length > 1) {
              let selected_entities = this.selectedEntities
              selectedEntitiesDownload(selected_entities)
            } else if (this.selectedEntities[0].is_group === 1) {
              folderDownload(this.selectedEntities[0])
            }
          },
          isEnabled: () => {
            if (
              this.selectedEntities?.length === 1 &&
              !this.selectedEntities[0]?.is_group
            ) {
              return false
            }
            if (this.selectedEntities?.length) {
              const allEntitiesSatisfyCondition = this.selectedEntities?.every(
                (entity) => {
                  return entity.allow_download || entity.owner === "You"
                }
              )
              return allEntitiesSatisfyCondition
            }
          },
        },
        {
          label: "Share",
          icon: Share,
          onClick: () => {
            this.emitter.emit("showShareDialog")
          },
          isEnabled: () => {
            return (
              this.$route.name === "Folder" &&
              this.$store.state.currentFolder[0]?.owner === "You"
            )
          },
        },
        {
          label: "Get Link",
          icon: Link,
          onClick: () => {
            getLink(this.selectedEntities[0])
          },
          isEnabled: () => {
            return this.selectedEntities?.length === 1
          },
        },
        {
          label: "Rename",
          icon: Rename,
          onClick: () => {
            this.showRenameDialog = true
          },
          isEnabled: () => {
            return (
              this.selectedEntities?.length === 1 &&
              (this.selectedEntities[0]?.write ||
                this.selectedEntities[0]?.owner === "You")
            )
          },
        },
        {
          label: "Favourite",
          icon: Star,
          onClick: () => {
            this.$resources.toggleFavourite.submit()
          },
          isEnabled: () => {
            return (
              this.selectedEntities?.length > 0 &&
              this.isLoggedIn &&
              this.selectedEntities?.every((x) => !x.is_favourite)
            )
          },
        },
        {
          label: "Unfavourite",
          icon: Star,
          onClick: () => {
            this.$resources.toggleFavourite.submit()
          },
          isEnabled: () => {
            return (
              this.selectedEntities?.length > 0 &&
              this.selectedEntities?.every((x) => x.is_favourite)
            )
          },
        },
      ].filter((item) => item.isEnabled())
    },
    fullName() {
      return this.$store.state.user.fullName
    },
    imageURL() {
      return this.$store.state.user.imageURL
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn
    },
    connectedUsers() {
      return this.$store.state.connectedUsers
    },
    currentViewEntites() {
      return this.$store.state.currentViewEntites
    },
    canUpload() {
      if (
        (this.$route.name === "Home" || this.$route.name === "Notifications") &&
        this.$store.state.currentFolderID === this.$store.state.homeFolderID
      ) {
        return false
      }
      if (
        this.$store.state.currentFolder[0]?.owner === "You" ||
        this.$store.state.currentFolder[0]?.write === 1
      ) {
        return false
      }
      return true
    },
  },
  methods: {
    handleSelectedEntity() {
      if (this.$route.name === "Folder") {
        return this.$store.commit(
          "setEntityInfo",
          this.$store.state.currentFolder
        )
      }
    },
  },
  resources: {
    createDocument() {
      return {
        url: "drive.api.files.create_document_entity",
        onSuccess(data) {
          data.modified = formatDate(data.modified)
          data.creation = formatDate(data.creation)
          this.$store.commit("setEntityInfo", [data])
          this.previewEntity = data
          data.owner = "You"
        },
        onError(data) {
          console.log(data)
        },
        auto: false,
      }
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
            !this.$store.state.entityInfo[0].is_favourite
        },
      }
    },
  },
}
</script>
