<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    class="bg-surface-white border-b w-full px-5 py-2.5 h-12 flex items-center justify-between"
  >
    <Breadcrumbs
      :items="store.state.breadcrumbs"
      :class="'select-none'"
    >
      <template #prefix="{ item, index }">
        <LoadingIndicator
          v-if="item.loading"
          width="20"
          scale="70"
        />
        <div
          v-if="index == 0"
          class="mr-1.5"
        >
          <component
            :is="COMPONENT_MAP[item.name]"
            class="size-4 text-ink-gray-6"
          />
        </div>
      </template>
    </Breadcrumbs>

    <div class="flex gap-2">
      <LucideStar
        v-if="rootEntity?.is_favourite"
        width="16"
        height="16"
        class="my-auto stroke-amber-500 fill-amber-500"
      />
      
      <div
        v-if="
          ['Folder', 'Home', 'Team'].includes($route.name) &&
          isLoggedIn &&
          props.rootResource?.data?.write
        "
        class="flex gap-2"
      >
        <Dropdown :options="uploadOptions" placement="left">
          <Button variant="subtle" class="rounded-lg px-3">
            <template #prefix>
              <LucideFolderUp class="size-4" />
            </template>
            Tải lên
          </Button>
        </Dropdown>
        <Dropdown :options="createOptions" placement="left">
          <Button variant="subtle" class="rounded-lg px-3">
            <template #prefix>
              <LucideFilePlus2 class="size-4" />
            </template>
            Mới
          </Button>
        </Dropdown>
      </div>
      <Button
        v-if="button"
        class="line-clamp-1 truncate w-full"
        :disabled="!button.entities.data?.length"
        variant="subtle"
        :theme="button.theme || 'gray'"
        @click="emitter.emit('showCTADelete')"
      >
        <template #prefix>
          <component
            :is="button.icon"
            class="size-4"
          />
        </template>
        {{ button.label }}
      </Button>

      <div
        v-if="connectedUsers.length > 1 && isLoggedIn"
        class="hidden sm:flex bg-surface-gray-3 rounded justify-center items-center px-1"
      >
        <UsersBar />
      </div>

      <div
        v-if="!isLoggedIn"
        class="ml-auto"
      >
        <Button
          variant="solid"
          @click="$router.push({ name: 'Login' })"
        >
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
import emitter from "@/emitter"
import {
  createDocument,
  getFavourites,
  getRecents,
  getTrash,
  toggleFav,
} from "@/resources/files"
import { entitiesDownload } from "@/utils/download"
import {
  Breadcrumbs,
  Button,
  Dropdown,
  LoadingIndicator
} from "frappe-ui"
import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"
import UsersBar from "./UsersBar.vue"

import LucideBuilding2 from "~icons/lucide/building-2"
import LucideClock from "~icons/lucide/clock"
import LucideDownload from "~icons/lucide/download"
import LucideFilePlus2 from "~icons/lucide/file-plus-2"
import LucideFileUp from "~icons/lucide/file-up"
import LucideFolderPlus from "~icons/lucide/folder-plus"
import LucideFolderUp from "~icons/lucide/folder-up"
import LucideHome from "~icons/lucide/home"
import LucideInfo from "~icons/lucide/info"
import LucideLink from "~icons/lucide/link"
import LucideMoveUpRight from "~icons/lucide/move-up-right"
import LucideShare2 from "~icons/lucide/share-2"
import LucideSquarePen from "~icons/lucide/square-pen"
import LucideStar from "~icons/lucide/star"
import LucideTrash from "~icons/lucide/trash"
import LucideUsers from "~icons/lucide/users"

const COMPONENT_MAP = {
  Home: LucideHome,
  Team: LucideBuilding2,
  Favourites: LucideStar,
  Shared: LucideUsers,
  Trash: LucideTrash,
  Recents: LucideClock,
}
const store = useStore()
const route = useRoute()
const router = useRouter()

const props = defineProps({
  actions: Array,
  triggerRoot: Function,
  rootResource: Object,
})
const isLoggedIn = computed(() => store.getters.isLoggedIn)
const connectedUsers = computed(() => store.state.connectedUsers)
const dialog = ref("")
const rootEntity = computed(() => props.rootResource?.data)

const dropdownAction = computed(() => {
  if (props.actions) return props.actions
  if (!rootEntity.value) return
  return [
    {
      label: __("Share"),
      icon: LucideShare2,
      onClick: () => (dialog.value = "s"),
      isEnabled: () => rootEntity.value.share,
    },
    {
      label: __("Download"),
      icon: LucideDownload,
      onClick: () => entitiesDownload(route.params.team, [rootEntity.value]),
    },
    {
      label: __("Copy Link"),
      icon: LucideLink,
      onClick: () => getLink(rootEntity.value),
    },
    { divider: true },
    {
      label: __("Move"),
      icon: LucideMoveUpRight,
      onClick: () => (dialog.value = "m"),
      isEnabled: () => rootEntity.value.write,
    },
    {
      label: __("Rename"),
      icon: LucideSquarePen,
      onClick: () => (dialog.value = "rn"),
      isEnabled: () => rootEntity.value.write,
    },
    {
      label: __("Show Info"),
      icon: LucideInfo,
      onClick: () => infoEntities.value.push(store.state.activeEntity),
      isEnabled: () => !store.state.activeEntity || !store.state.showInfo,
    },
    {
      label: __("Hide Info"),
      icon: LucideInfo,
      onClick: () => (dialog.value = "info"),
      isEnabled: () => store.state.activeEntity && store.state.showInfo,
    },
    {
      label: __("Favourite"),
      icon: LucideStar,
      onClick: () => {
        rootEntity.value.is_favourite = true
        toggleFav.submit({
          entities: [{ name: rootEntity.value.name, is_favourite: false }],
        })
      },
      isEnabled: () => !rootEntity.value.is_favourite,
    },
    {
      label: __("Unfavourite"),
      icon: LucideStar,
      color: "stroke-amber-500 fill-amber-500",
      onClick: () => {
        rootEntity.value.is_favourite = false
        toggleFav.submit({
          entities: [{ name: rootEntity.value.name, is_favourite: false }],
        })
      },
      isEnabled: () => rootEntity.value.is_favourite,
    },
    { divider: true },
    {
      label: __("Delete"),
      icon: LucideTrash,
      onClick: () => (dialog.value = "remove"),
      isEnabled: () => rootEntity.value.write,
      color: "text-ink-red-4",
    },
  ].filter((k) => !k.isEnabled || k.isEnabled())
})

// Functions
const newDocument = async () => {
  let data = await createDocument.submit({
    title: __("Untitled Document"),
    team: route.params.team,
    personal: store.state.breadcrumbs[0].name === "Home" ? 1 : 0,
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
  {
    route: "Recents",
    label: __("Clear"),
    icon: LucideClock,
    entities: getRecents,
  },
  {
    route: "Favourites",
    label: __("Clear"),
    icon: LucideStar,
    entities: getFavourites,
  },
  {
    route: "Trash",
    label: __("Empty"),
    icon: LucideTrash,
    entities: getTrash,
    theme: "red",
  },
]
const button = computed(() =>
  possibleButtons.find((k) => k.route == route.name)
)

const uploadOptions = [
  {
    label: __("Upload File"),
    icon: LucideFileUp,
    onClick: () => emitter.emit("uploadFile"),
  },
  {
    label: __("Upload Folder"),
    icon: LucideFolderUp,
    onClick: () => emitter.emit("uploadFolder"),
  },
]

const createOptions = [
  {
    label: __("Document"),
    icon: LucideFilePlus2,
    onClick: newDocument,
  },
  {
    label: __("Folder"),
    icon: LucideFolderPlus,
    onClick: () => emitter.emit("newFolder"),
  },
  {
    label: __("New Link"),
    icon: LucideLink,
    onClick: () => emitter.emit("newLink"),
  },
]
</script>
