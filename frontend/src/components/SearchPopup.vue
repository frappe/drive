<template>
  <Dialog v-model:open="open" :options="{ size: '2xl', position: 'top' }">
    <template #body>
      <div class="flex px-4 py-3 gap-1 items-center border-b">
        <Search class="w-4 mr-1 h-auto" name="search" />
        <input
          v-model="search"
          icon-left="search"
          type="text"
          class="appearance-none forced-colors:hidden w-full border-none bg-transparent py-3 pl-11.5 pr-4.5 text-base text-gray-800 placeholder-gray-500 focus:ring-0"
          placeholder="Search"
        />
      </div>
      <div
        v-if="$resources.entities.data?.length"
        class="flex flex-col py-4 px-2.5 overflow-y-auto overflow-x-auto max-h-[50vh]"
      >
        <span class="mb-1 pl-2 text-base text-gray-600"
          >Search results for <strong>"{{ search }}"</strong></span
        >
        <div
          v-for="entity in $resources.entities.data"
          :key="entity.name"
          class="grid grid-flow-col grid-cols-8 gap-2 w-full items-center rounded px-2 py-2 text-base cursor-pointer hover:bg-gray-100"
          @click="openEntity(entity)"
        >
          <div class="flex items-center gap-2 w-full col-span-6">
            <svg
              v-if="entity.is_group"
              class="h-4 w-4"
              :draggable="false"
              :style="{ fill: entity.color }"
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g clip-path="url(#clip0_1942_59507)">
                <path
                  d="M7.83412 2.88462H1.5C1.22386 2.88462 1 3.10847 1 3.38462V12.5C1 13.6046 1.89543 14.5 3 14.5H13C14.1046 14.5 15 13.6046 15 12.5V2C15 1.72386 14.7761 1.5 14.5 1.5H9.94008C9.88623 1.5 9.83382 1.51739 9.79065 1.54957L8.13298 2.78547C8.04664 2.84984 7.94182 2.88462 7.83412 2.88462Z"
                />
              </g>
              <defs>
                <clipPath id="clip0_1942_59507">
                  <rect width="16" height="16" fill="white" />
                </clipPath>
              </defs>
            </svg>
            <img
              v-else
              class="w-4 h-4"
              :src="getIconUrl(formatMimeType(entity.mime_type))"
            />
            <span class="truncate">{{ entity.title }}</span>
          </div>
          <div
            class="col-span-2 grid grid-flow-col justify-start items-center truncate"
          >
            <Avatar
              :image="entity.user_image"
              :label="entity.full_name"
              class="relative mr-2"
              size="xs"
            />
            <span class="text-base text-gray-800">{{ entity.full_name }}</span>
          </div>
        </div>
      </div>
      <div
        v-if="search.length > 3 && !$resources.entities.data?.length"
        class="flex flex-col py-4 px-2.5"
      >
        <span class="mb-1 pl-2 text-base text-gray-600"
          >No results for <strong>"{{ search }}"</strong></span
        >
      </div>
      <div
        v-if="!$resources.entities.data?.length && !search.length"
        class="flex flex-col mb-2 mt-4 first:mt-3"
      >
        <span class="mb-1 px-4.5 text-base text-gray-600">Jump to</span>
        <div class="px-2.5">
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100"
            @click="
              $router.push({ name: 'Home' }),
                emitter.emit('showSearchPopup', false)
            "
          >
            <Home class="mr-2 h-4 w-4 text-gray-700" />
            Home
          </div>
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100"
            @click="
              $router.push({ name: 'Recents' }),
                emitter.emit('showSearchPopup', false)
            "
          >
            <Recent class="mr-2 h-4 w-4 text-gray-700" />
            Recents
          </div>
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100"
            @click="
              $router.push({ name: 'Favourites' }),
                emitter.emit('showSearchPopup', false)
            "
          >
            <Star class="mr-2 h-4 w-4 text-gray-700" />
            Favourites
          </div>
        </div>
        <span class="mt-3 mb-1 px-4.5 text-base text-gray-600">Actions</span>
        <div class="px-2.5">
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100"
            @click="
              emitter.emit('uploadFile'), emitter.emit('showSearchPopup', false)
            "
          >
            <FileUpload class="stroke-[1.35] mr-2 h-4 w-4 text-gray-700" />
            Upload File
          </div>
          <div
            class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100"
            @click="
              emitter.emit('uploadFolder'),
                emitter.emit('showSearchPopup', false)
            "
          >
            <FolderUpload class="stroke-[1.35] mr-2 h-4 w-4 text-gray-700" />
            Upload Folder
          </div>
          <!--       <div class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100">
        <FeatherIcon name="folder-plus" class="mr-2 h-4 w-4 text-gray-700"/>
        New Folder
      </div>
      <div class="flex w-full min-w-0 items-center rounded px-2 py-2 text-base font-medium text-gray-700 hover:bg-gray-100">
        <FeatherIcon name="file-text" class="mr-2 h-4 w-4 text-gray-700"/>
        New Document
      </div> -->
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script>
import Home from "./EspressoIcons/Home.vue"
import Recent from "./EspressoIcons/Recent.vue"
import Search from "./EspressoIcons/Search.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import { Dialog, Avatar } from "frappe-ui"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import Star from "./EspressoIcons/Star.vue"

export default {
  name: "SearchPopup",
  components: {
    Dialog,
    Avatar,
    Home,
    Recent,
    Search,
    Star,
    FileUpload,
    FolderUpload,
  },
  emits: ["openEntity", "update:open"],
  setup() {
    return { formatMimeType, getIconUrl }
  },
  data() {
    return {
      isOpen: false,
      search: "",
      selectedEntity: "",
    }
  },
  computed: {
    fullName() {
      return this.$store.state.user.fullName
    },
    open: {
      get() {
        return this.open
      },
      set(value) {
        this.$emit("update:open", value)
      },
    },
  },
  watch: {
    search: {
      handler(value) {
        if (value.length >= 3) {
          this.search = value
          this.$resources.entities.submit({
            query: value,
            home_dir: this.$store.state.homeFolderID,
          })
        } else {
          this.$resources.entities.reset()
        }
      },
    },
  },
  methods: {
    openEntity(entity) {
      this.$resources.upwardPath
        .fetch({ entity_name: entity.name })
        .then(() => {
          if (entity.is_group) {
            this.selectedEntities = []
            this.$router.push({
              name: "Folder",
              params: { entityName: entity.name },
            })
          } else if (entity.document) {
            this.$router.push({
              name: "Document",
              params: { entityName: entity.name },
            })
          } else {
            this.$router.push({
              name: "File",
              params: { entityName: entity.name },
            })
          }
        })
      this.emitter.emit("showSearchPopup", false)
    },
  },
  resources: {
    entities() {
      return {
        auto: false,
        method: "POST",
        url: "drive.api.files.search",
      }
    },
    upwardPath() {
      return {
        auto: false,
        method: "POST",
        url: "drive.api.files.generate_upward_path",
      }
    },
  },
}
</script>

<style scoped>
input {
  all: unset;
}
input:focus {
  all: unset;
  outline: none;
  border: none;
}
</style>
