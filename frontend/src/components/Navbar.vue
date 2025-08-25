<template>
  <nav
    ondragstart="return false;"
    ondrop="return false;"
    id="navbar"
    class="bg-surface-white border-b px-5 py-2.5 h-12 flex items-center justify-between"
  >
    <div class="flex justify-center items-center">
      <div
        id="navbar-prefix"
        class="mr-2"
      />
      <Breadcrumbs
        :items="store.state.breadcrumbs"
        class="select-none truncate"
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
    </div>

    <div class="flex gap-2">
      <div
        id="navbar-content"
        class="flex items-center"
      />
      <LucideStar
        v-if="rootEntity?.is_favourite"
        width="16"
        height="16"
        class="my-auto stroke-amber-500 fill-amber-500"
      />
      <template v-if="!isLoggedIn">
        <Button
          label="Download"
          variant="outline"
          @click="entitiesDownload($route.params.team, [rootEntity])"
        />
        <Button
          variant="solid"
          @click="$router.push({ name: 'Login' })"
        >
          Sign In
        </Button>
      </template>
      <Dropdown
        v-else-if="defaultActions"
        :options="defaultActions"
        placement="right"
        :button="{
          variant: 'ghost',
          onClick: () => {
            $store.commit('setActiveEntity', rootEntity)
          },
          icon: LucideMoreHorizontal,
        }"
      />

      <Dropdown
        v-if="
          ['Folder', 'Home', 'Team'].includes($route.name) &&
          isLoggedIn &&
          props.rootResource?.data?.write !== false
        "
        :button="{
          variant: 'solid',
          icon: LucidePlus,
        }"
        :options="newEntityOptions"
        placement="right"
      />
      <Button
        v-if="button"
        :disabled="!button.entities.data?.length"
        :theme="button.theme || 'gray'"
        @click="dialog = 'cta-' + $route.name.toLowerCase()"
      >
        <template #prefix>
          <component
            :is="button.icon"
            class="size-4"
          />
        </template>
        {{ button.label }}
      </Button>
    </div>
    <Button
      v-if="!isLoggedIn"
      class="fixed bottom-4 right-4 text-sm"
      variant="outline"
      :icon-left="h(FrappeDriveLogo, { class: 'w-4.5 h-4.5' })"
      label="Try out Drive"
      @click="open('https://frappe.io/drive')"
    />
    <Dialogs
      v-model="dialog"
      :entities="entities?.length ? entities : [rootEntity]"
    />
  </nav>
</template>
<script setup>
import {
  Button,
  Breadcrumbs,
  LoadingIndicator,
  Dropdown,
  toast,
} from "frappe-ui"
import { useStore } from "vuex"
import emitter from "@/emitter"
import { ref, computed, inject, h } from "vue"
import { entitiesDownload } from "@/utils/download"
import {
  getRecents,
  getFavourites,
  getTrash,
  createDocument,
  toggleFav,
  getDocuments,
} from "@/resources/files"
import { useRoute, useRouter } from "vue-router"
import { getLink, prettyData } from "@/utils/files"

import LucideClock from "~icons/lucide/clock"
import LucideHome from "~icons/lucide/home"
import LucideTrash from "~icons/lucide/trash"
import LucideUsers from "~icons/lucide/users"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideStar from "~icons/lucide/star"
import LucideMoreHorizontal from "~icons/lucide/more-horizontal"
import LucideShare2 from "~icons/lucide/share-2"
import LucideDownload from "~icons/lucide/download"
import LucidePlus from "~icons/lucide/plus"
import LucideLink from "~icons/lucide/link"
import LucideArrowLeftRight from "~icons/lucide/arrow-left-right"
import LucideSquarePen from "~icons/lucide/square-pen"
import LucideInfo from "~icons/lucide/info"
import LucideFileUp from "~icons/lucide/file-up"
import LucideFolderUp from "~icons/lucide/folder-up"
import LucideFilePlus2 from "~icons/lucide/file-plus-2"
import LucideFolderPlus from "~icons/lucide/folder-plus"
import FrappeDriveLogo from "./FrappeDriveLogo.vue"

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
const open = (url) => {
  window.open(url, "_blank")
}

const props = defineProps({
  rootResource: Object,
  actions: { type: Array, required: false },
  // Used to pass into dialogs
  entities: {
    type: Array,
    default: [],
  },
})

const isLoggedIn = computed(() => store.getters.isLoggedIn)
const dialog = inject("dialog", ref(""))
const rootEntity = computed(
  () => props.rootResource?.data?.title && props.rootResource?.data
)

const defaultActions = computed(() => {
  if (!rootEntity.value?.title) return
  let actions = []
  if (props.actions) {
    if (props.actions[0] === "extend") actions = props.actions.slice(1)
    else return props.actions
  }
  return [
    {
      group: true,
      hideLabel: true,
      items: [
        {
          label: __("Share"),
          icon: LucideShare2,
          onClick: () => {
            dialog.value = "s"
          },
          isEnabled: () => rootEntity.value.share,
        },
        {
          label: __("Download"),
          icon: LucideDownload,
          onClick: () =>
            entitiesDownload(route.params.team, [rootEntity.value]),
        },
        {
          label: __("Copy Link"),
          icon: LucideLink,
          onClick: () => getLink(rootEntity.value),
        },
      ],
    },
    {
      group: true,
      hideLabel: true,
      items: [
        {
          label: __("Move"),
          icon: LucideArrowLeftRight,
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
          onClick: () => (dialog.value = "i"),
          isEnabled: () => !store.state.activeEntity || !store.state.showInfo,
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
      ],
    },
    {
      group: true,
      hideLabel: true,
      items: [
        {
          label: __("Delete"),
          icon: LucideTrash,
          onClick: () => (dialog.value = "remove"),
          isEnabled: () => rootEntity.value.write,
          theme: "red",
        },
      ],
    },
    ...actions,
  ].map((k) => {
    return { ...k, items: k.items.filter((l) => !l.isEnabled || l.isEnabled()) }
  })
})

// Functions
const newDocument = async () => {
  toast.promise(
    createDocument.submit({
      title: "Untitled Document",
      team: route.params.team,
      personal: store.state.breadcrumbs[0].name === "Home" ? 1 : 0,
      content: null,
      parent: store.state.currentFolder.name,
    }),
    {
      successDuration: 1,
      loading: "Creating document...",
      success: (data) => {
        prettyData([data])
        data.file_type = "Document"
        store.state.listResource.data?.push?.(data)
        getDocuments.data?.push(data)
        window.open(
          router.resolve({
            name: "Document",
            params: { team: route.params.team, entityName: data.name },
          }).href
        )
        return "Created"
      },
      error: "Failed to create document",
    }
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
        onClick: () => (dialog.value = "f"),
      },
      {
        label: "New Link",
        icon: LucideLink,
        onClick: () => (dialog.value = "l"),
      },
    ],
  },
]
</script>
<style>
#navbar-prefix:empty {
  margin: 0;
}
</style>
