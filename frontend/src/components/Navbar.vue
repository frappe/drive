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
      <FeatherIcon
        v-if="rootEntity?.is_favourite"
        name="star"
        width="16"
        height="16"
        class="my-auto stroke-amber-500 fill-amber-500"
      />
      <Dropdown :options="genericActions" v-if="genericActions">
        <Button variant="ghost" @click="triggerRoot">
          <FeatherIcon name="more-horizontal" class="h-4 w-4" />
        </Button>
      </Dropdown>
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
    <Dialogs
      v-if="$route.name === 'File' || $route.name === 'Document'"
      v-model="dialog"
      :root-resource
    />
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
import { ref, computed } from "vue"
import {
  getRecents,
  getFavourites,
  getTrash,
  createDocument,
  toggleFav,
} from "@/resources/files"
import { useRoute, useRouter } from "vue-router"
import Share from "./EspressoIcons/ShareNew.vue"
import Download from "./EspressoIcons/Download.vue"
import Rename from "./EspressoIcons/Rename.vue"
import Move from "./EspressoIcons/Move.vue"
import Info from "./EspressoIcons/Info.vue"
import Trash from "./EspressoIcons/Trash.vue"

const store = useStore()
const route = useRoute()
const router = useRouter()

const props = defineProps({
  rootActions: Array,
  triggerRoot: Function,
  rootResource: Object,
})
const isLoggedIn = computed(() => store.getters.isLoggedIn)
const connectedUsers = computed(() => store.state.connectedUsers)
const dialog = ref("")
const rootEntity = computed(() => props.rootResource?.data)

const genericActions = computed(
  () =>
    rootEntity.value &&
    [
      {
        label: "Share",
        icon: Share,
        onClick: () => (dialog.value = "s"),
        isEnabled: () => rootEntity.value.share,
      },
      {
        label: "Download",
        icon: Download,
        onClick: (entities) => entitiesDownload(team, entities),
      },
      {
        label: "Copy Link",
        icon: Link,
        onClick: ([entity]) => getLink(entity),
      },
      { label: "Divider" },
      {
        label: "Move",
        icon: Move,
        onClick: () => (dialog.value = "m"),
        isEnabled: () => rootEntity.value.write,
      },
      {
        label: "Rename",
        icon: Rename,
        onClick: () => (dialog.value = "rn"),
        isEnabled: () => rootEntity.value.write,
      },
      {
        label: "Show Info",
        icon: Info,
        onClick: () => infoEntities.value.push(store.state.activeEntity),
        isEnabled: () => !store.state.activeEntity || !store.state.showInfo,
      },
      {
        label: "Hide Info",
        icon: Info,
        onClick: () => (dialog.value = "info"),
        isEnabled: () => store.state.activeEntity && store.state.showInfo,
      },
      {
        label: "Favourite",
        icon: "star",
        onClick: () => {
          rootEntity.value.is_favourite = true
          toggleFav.submit({
            entities: [{ name: rootEntity.value.name, is_favourite: false }],
          })
        },
        isEnabled: () => !rootEntity.value.is_favourite,
      },
      {
        label: "Unfavourite",
        icon: "star",
        class: "stroke-amber-500 fill-amber-500",
        onClick: () => {
          rootEntity.value.is_favourite = false
          toggleFav.submit({
            entities: [{ name: rootEntity.value.name, is_favourite: false }],
          })
        },
        isEnabled: () => rootEntity.value.is_favourite,
      },

      { label: "Divider" },
      {
        label: "Move to Trash",
        icon: Trash,
        onClick: () => (dialog.value = "remove"),
        isEnabled: () => rootEntity.value.write,
        danger: true,
      },
    ].filter((k) => k.isEnabled?.())
)

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
