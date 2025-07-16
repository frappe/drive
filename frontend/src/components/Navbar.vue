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
      <Dropdown
        v-if="dropdownAction"
        :options="dropdownAction"
      >
        <Button
          variant="ghost"
          @click="triggerRoot"
        >
          <LucideMoreHorizontal
            name="more-horizontal"
            class="size-4"
          />
        </Button>
      </Dropdown>
      <Dropdown
        v-if="
          ['Folder', 'Home', 'Team'].includes($route.name) &&
          isLoggedIn &&
          props.rootResource?.data?.write !== false
        "
        :options="newEntityOptions"
        placement="left"
        class="basis-5/12 lg:basis-auto"
      >
        <Tooltip text="Add or upload">
          <Button variant="solid">
            <div class="flex">
              <LucidePlus class="size-4" />
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
import UsersBar from "./UsersBar.vue"
import {
  Button,
  Breadcrumbs,
  LoadingIndicator,
  Dropdown,
  Tooltip,
} from "frappe-ui"
import { useStore } from "vuex"
import emitter from "@/emitter"
import { ref, computed } from "vue"
import { entitiesDownload } from "@/utils/download"
import {
  getRecents,
  getFavourites,
  getTrash,
  createDocument,
  toggleFav,
} from "@/resources/files"
import { useRoute, useRouter } from "vue-router"
import { getLink } from "@/utils/files"

import LucideClock from "~icons/lucide/clock"
import LucideHome from "~icons/lucide/home"
import LucideTrash from "~icons/lucide/trash"
import LucideUsers from "~icons/lucide/users"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideStar from "~icons/lucide/star"
import LucideShare2 from "~icons/lucide/share-2"
import LucideDownload from "~icons/lucide/download"
import LucideLink from "~icons/lucide/link"
import LucideMoveUpRight from "~icons/lucide/move-up-right"
import LucideSquarePen from "~icons/lucide/square-pen"
import LucideInfo from "~icons/lucide/info"
import LucideFileUp from "~icons/lucide/file-up"
import LucideFolderUp from "~icons/lucide/folder-up"
import LucideFilePlus2 from "~icons/lucide/file-plus-2"
import LucideFolderPlus from "~icons/lucide/folder-plus"

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
  if (!rootEntity.value?.title) return
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
      theme: "red",
    },
  ].filter((k) => !k.isEnabled || k.isEnabled())
})

// Functions
const newDocument = async () => {
  let data = await createDocument.submit({
    title: "Untitled Document",
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

const newEntityOptions = [
  {
    group: "Upload",
    items: [
      {
        label: "Upload File",
        icon: LucideFileUp,
        onClick: () => emitter.emit("uploadFile"),
      },
      {
        label: "Upload Folder",
        icon: LucideFolderUp,
        onClick: () => emitter.emit("uploadFolder"),
      },
    ],
  },
  {
    group: "Create",
    items: [
      {
        label: "Document",
        icon: LucideFilePlus2,
        onClick: newDocument,
      },
      {
        label: "Folder",
        icon: LucideFolderPlus,
        onClick: () => emitter.emit("newFolder"),
      },

      {
        label: "New Link",
        icon: LucideLink,
        onClick: () => emitter.emit("newLink"),
      },
    ],
  },
]
</script>
