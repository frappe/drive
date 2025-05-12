<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-white border-b w-full px-4 py-2.5 h-12 flex items-center justify-between"
  >
    <Breadcrumbs :items="store.state.breadcrumbs" :class="'select-none'">
      <template #prefix="{ item }">
        <LoadingIndicator v-if="item.loading" scale="70" />
      </template>
    </Breadcrumbs>
    <div class="flex gap-2">
      <Dropdown
        v-if="['Folder', 'Home', 'Team'].includes($route.name) && isLoggedIn"
        :options="newEntityOptions"
        placement="left"
        class="basis-5/12 lg:basis-auto"
      >
        <Tooltip text="Add or upload">
          <Button variant="solid">
            <div class="flex">
              <FeatherIcon name="plus" class="w-4 h-4" />
            </div>
          </Button>
        </Tooltip>
      </Dropdown>
      <Button
        v-if="button"
        class="line-clamp-1 truncate w-full"
        :disabled="!button.entities.data?.length"
        variant="subtle"
        :theme="button.theme || 'gray'"
        @click="emitter.emit('showCTADelete')"
      >
        <template #prefix>
          <FeatherIcon :name="button.icon" class="w-4" />
        </template>
        {{ button.label }}
      </Button>
      <div
        v-if="connectedUsers.length > 1 && isLoggedIn"
        class="hidden sm:flex bg-gray-200 rounded justify-center items-center px-1"
      >
        <UsersBar />
      </div>

      <div v-if="!isLoggedIn" class="ml-auto">
        <Button variant="solid" @click="$router.push({ name: 'Login' })">
          Sign In
        </Button>
      </div>
    </div>
  </nav>
</template>
<script setup>
import UsersBar from "./UsersBar.vue"
import {
  Button,
  Breadcrumbs,
  LoadingIndicator,
  FeatherIcon,
  Dropdown,
  Tooltip,
} from "frappe-ui"
import { useStore } from "vuex"
import NewFolder from "./EspressoIcons/NewFolder.vue"
import Link from "./EspressoIcons/Link.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import NewFile from "./EspressoIcons/NewFile.vue"
import emitter from "@/emitter"
import { computed } from "vue"
import {
  getRecents,
  getFavourites,
  getTrash,
  createDocument,
} from "@/resources/files"
import { useRoute, useRouter } from "vue-router"

const store = useStore()
const route = useRoute()
const router = useRouter()

const isLoggedIn = computed(() => store.getters.isLoggedIn)
const connectedUsers = computed(() => store.state.connectedUsers)

// onMounted(() => {
//   for (let element of document.getElementsByTagName("button")) {
//     element.classList.remove("focus:ring-2", "focus:ring-offset-2")
//   }
// })

// Functions
const newDocument = async () => {
  let data = await createDocument.submit({
    title: "Untitled Document",
    team: route.params.team,
    personal: store.state.breadcrumbs[0].label === "Home" ? 1 : 0,
    content: null,
    parent: store.state.currentFolder.name,
  })
  window.open(
    router.resolve({
      name: "Document",
      params: { team: route.params.team, entityName: data.name },
    }).href
  )
}

// Constants
const possibleButtons = [
  { route: "Recents", label: "Clear", icon: "clock", entities: getRecents },
  {
    route: "Favourites",
    label: "Clear",
    icon: "star",
    entities: getFavourites,
  },
  {
    route: "Trash",
    label: "Empty",
    icon: "trash",
    entities: getTrash,
    theme: "red",
  },
]
const button = computed(() =>
  possibleButtons.find((k) => k.route == route.name)
)

const newEntityOptions = [
  {
    group: "Upload",
    items: [
      {
        label: "Upload File",
        icon: FileUpload,
        onClick: () => emitter.emit("uploadFile"),
      },
      {
        label: "Upload Folder",
        icon: FolderUpload,
        onClick: () => emitter.emit("uploadFolder"),
      },
    ],
  },
  {
    group: "Create",
    items: [
      {
        label: "Document",
        icon: NewFile,
        onClick: newDocument,
      },
      {
        label: "Folder",
        icon: NewFolder,
        onClick: () => emitter.emit("newFolder"),
      },

      {
        label: "New Link",
        icon: Link,
        onClick: () => emitter.emit("newLink"),
      },
    ],
  },
]
</script>
