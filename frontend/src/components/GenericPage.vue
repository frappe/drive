<template>
  <Navbar
    v-if="!verify?.error && !getEntities.error"
    :root-resource="verify"
    :entities="activeEntity ? [activeEntity] : selectedEntitities"
  />

  <ErrorPage
    v-if="verify?.error || getEntities.error"
    :error="verify?.error || getEntities.error"
  />

  <div
    v-else
    id="drop-area"
    ref="container"
    class="flex flex-col overflow-auto min-h-full bg-surface-white"
  >
    <DriveToolBar
      v-model:sort-order="sortOrder"
      v-model:search="search"
      v-model:filters="filters"
      v-model:team="team"
      :action-items="actionItems"
      :selections="selectedEntitities"
      :get-entities="getEntities || { data: [] }"
    />

    <div
      v-if="!props.getEntities.data"
      class="m-auto"
      style="transform: translate(0, -88.5px)"
    >
      <LoadingIndicator class="size-5 text-ink-gray-9" />
    </div>
    <NoFilesSection
      v-else-if="!props.getEntities.data?.length"
      :icon="icon"
      v-bind="empty"
    />
    <ListView
      v-else-if="$store.state.view === 'list'"
      v-model="selections"
      :folder-contents="rows && grouper(rows)"
      :action-items="actionItems"
      :user-data="userData"
      :root-entity="verify?.data"
      @dropped="onDrop"
    />
    <GridView
      v-else
      v-model="selections"
      :folder-contents="rows"
      :action-items="actionItems"
      :user-data="userData"
      @dropped="onDrop"
    />
  </div>
  <p
    class="hidden absolute text-center top-1/2 left-[calc(50%-4rem)] w-32 z-10 font-bold"
  >
    Drop to upload
  </p>
  <Transition
    v-if="store.state.uploads.length > 0"
    enter-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    enter-from-class="translate-y-1 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-[150ms] ease-[cubic-bezier(.21,1.02,.73,1)]"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-1 opacity-0"
  >
    <UploadTracker />
  </Transition>
</template>
<script setup>
import ListView from "@/components/ListView.vue"
import GridView from "@/components/GridView.vue"
import DriveToolBar from "@/components/DriveToolBar.vue"
import Navbar from "@/components/Navbar.vue"
import NoFilesSection from "@/components/NoFilesSection.vue"
import UploadTracker from "@/components/UploadTracker.vue"
import ErrorPage from "@/components/ErrorPage.vue"
import { getLink, pasteObj } from "@/utils/files"
import { toggleFav, clearRecent } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { entitiesDownload } from "@/utils/download"
import { ref, computed, watch, watchEffect, provide, inject } from "vue"
import { useRoute } from "vue-router"
import { useEventListener } from "@vueuse/core"
import { useStore } from "vuex"
import { openEntity } from "@/utils/files"
import { toast } from "@/utils/toasts"
import { move } from "@/resources/files"
import { LoadingIndicator } from "frappe-ui"
import { settings } from "@/resources/permissions"
import emitter from "@/emitter"

import LucideClock from "~icons/lucide/clock"
import LucideDownload from "~icons/lucide/download"
import LucideExternalLink from "~icons/lucide/external-link"
import LucideEye from "~icons/lucide/eye"
import LucideInfo from "~icons/lucide/info"
import LucideLink2 from "~icons/lucide/link-2"
import LucideArrowLeftRight from "~icons/lucide/arrow-left-right"
import LucideRotateCcw from "~icons/lucide/rotate-ccw"
import LucideShare2 from "~icons/lucide/share-2"
import LucideSquarePen from "~icons/lucide/square-pen"
import LucideStar from "~icons/lucide/star"
import LucideTrash from "~icons/lucide/trash"
import { prettyData, sortEntities } from "@/utils/files"

const props = defineProps({
  grouper: { type: Function, default: (d) => d },
  showSort: { type: Boolean, default: true },
  verify: { type: Object, default: null },
  icon: [Function, Object],
  empty: Object,
  getEntities: Object,
})
const route = useRoute()
const store = useStore()

const dialog = ref("")
provide("dialog", dialog)

const team = ref(
  ["Shared", "Recents", "Favourites", "Trash"].includes(route.name)
    ? "all"
    : route.params.team
)
watch(
  () => route.params.team,
  (v) => {
    team.value = v || ""
  },
  { immediate: true }
)
watch(
  [team, () => props.getEntities.data?.[0]?.team],
  ([v, v2]) => (v || v2) && allUsers.fetch({ team: v || v2 }),
  { immediate: true }
)
const activeEntity = computed(() => store.state.activeEntity)

const sortId = computed(
  () =>
    props.getEntities.params?.entity_name || props.getEntities.params?.personal
)
const sortOrder = ref(
  store.state.sortOrder[sortId.value] || {
    label: "Modified",
    field: "modified",
    ascending: false,
  }
)
const search = ref("")
const filters = ref([])

const rows = ref(props.getEntities.data)
watch(sortId, (id) => {
  if (store.state.sortOrder[id]) sortOrder.value = store.state.sortOrder[id]
})

watch(
  sortOrder,
  (order) => {
    rows.value = sortEntities([...rows.value], order)
    props.getEntities.setData(rows.value)
    if (sortId.value) {
      store.commit("setSortOrder", [sortId.value, order])
    }
  },
  { deep: true }
)

watch(search, (val) => {
  const search = new RegExp(val, "i")
  rows.value = props.getEntities.data.filter((k) => search.test(k.title))
})

watch(
  () => filters.value,
  (val) => {
    if (!val.length) {
      rows.value = props.getEntities.data
      return
    }
    const file_types = val.map((k) => k.name)
    const isFolder = file_types.find((k) => k === "Folder")
    rows.value = props.getEntities.data.filter(
      ({ file_type, is_group }) =>
        file_types.includes(file_type) || (isFolder && is_group)
    )
  },
  { deep: true }
)

watch(
  () => props.getEntities.data,
  (val) => {
    if (!val) return
    rows.value = sortEntities([...val], sortOrder.value)
    store.commit("setCurrentFolder", {
      entities: rows.value.filter?.((k) => k.title[0] !== "."),
    })
  },
  { immediate: true, deep: true }
)

store.commit("setListResource", props.getEntities)
store.commit("setCurrentResource", null)

const selections = ref(new Set())
const selectedEntitities = computed(
  () =>
    props.getEntities.data?.filter?.(({ name }) =>
      selections.value.has(name)
    ) || []
)

const verifyAccess = computed(() => props.verify?.data || !props.verify)
watchEffect(() => {
  if (verifyAccess.value?.write) useEventListener("paste", pasteObj)
})

const refreshData = () => {
  const params = { team: team.value === "home" ? "" : team.value || "" }
  if (sortOrder.value)
    params.order_by =
      sortOrder.value.field + (sortOrder.value.ascending ? " 1" : " 0")
  props.getEntities.fetch({ ...props.getEntities.params, ...params })
}

watch(
  [verifyAccess, team],
  ([data]) => {
    if (!data) return
    refreshData()
  },
  { immediate: true, deep: false }
)
emitter.on("refresh", refreshData)
emitter.on("remove-file", (item) => {
  console.log("alo")
  selections.value.clear()
  selections.value.add(item)
  dialog.value = "remove"
})

if (team.value && !allUsers.fetched && store.getters.isLoggedIn) {
  allUsers.fetch({ team: team.value })
}
if (!settings.fetched && store.getters.isLoggedIn) settings.fetch()

// Drag and drop
const removeFile = (file, target) => {
  const removedIndex = props.getEntities.data.findIndex((k) => k.name === file)
  props.getEntities.data.splice(removedIndex, 1)
  const targetRow = props.getEntities.data.find((k) => k.name === target)
  if (targetRow) targetRow.children += 1
  props.getEntities.setData(props.getEntities.data)
}
const onDrop = (targetFile, draggedItem) => {
  if (!targetFile.is_group || draggedItem === targetFile.name || !draggedItem)
    return
  move.submit({
    entity_names: [draggedItem],
    new_parent: targetFile.name,
  })
  removeFile(draggedItem, targetFile.name)
}
emitter.on("remove-file-ui", removeFile)

// Action Items
const actionItems = computed(() => {
  if (route.name === "Trash") {
    return [
      {
        label: "Restore",
        icon: LucideRotateCcw,
        action: () => (dialog.value = "restore"),
        multi: true,
        important: true,
      },
      {
        label: "Delete forever",
        icon: LucideTrash,
        action: () => (dialog.value = "d"),
        isEnabled: () => route.name === "Trash",
        multi: true,
        danger: true,
      },
    ].filter((a) => !a.isEnabled || a.isEnabled())
  } else {
    return [
      {
        label: __("Preview"),
        icon: LucideEye,
        action: ([entity]) => openEntity(entity),
        isEnabled: (e) => !e.is_link,
      },
      {
        label: __("Open"),
        icon: LucideExternalLink,
        action: ([entity]) => openEntity(entity),
        isEnabled: (e) => e.is_link,
      },
      { divider: true },
      {
        label: __("Share"),
        icon: LucideShare2,
        action: () => (dialog.value = "s"),
        isEnabled: (e) => e.share,
        important: true,
      },
      {
        label: __("Download"),
        icon: LucideDownload,
        isEnabled: (e) =>
          !e.is_link && e.mime_type !== "frappe/slides" && e.allow_download,
        action: (entities) => entitiesDownload(team.value, entities),
        multi: true,
        important: true,
      },
      {
        label: __("Copy Link"),
        icon: LucideLink2,
        action: ([entity]) => getLink(entity),
        important: true,
      },
      { divider: true, isEnabled: (e) => !e.external },
      {
        label: __("Move"),
        icon: LucideArrowLeftRight,
        action: () => (dialog.value = "m"),
        isEnabled: (e) => e.write,
        multi: true,
        important: true,
      },
      {
        label: __("Rename"),
        icon: LucideSquarePen,
        action: () => (dialog.value = "rn"),
        isEnabled: (e) => e.write,
      },
      {
        label: __("Show Info"),
        icon: LucideInfo,
        action: () => (dialog.value = "i"),
        isEnabled: (e) =>
          !store.state.activeEntity || (!store.state.showInfo && !e.external),
      },
      {
        label: __("Favourite"),
        icon: LucideStar,
        action: (entities) => {
          entities.forEach((e) => (e.is_favourite = true))
          // Hack to cache
          props.getEntities.setData(props.getEntities.data)
          toggleFav.submit({ entities })
        },
        isEnabled: (e) => !e.is_favourite && !e.external,
        important: true,
        multi: true,
      },
      {
        label: __("Unfavourite"),
        icon: LucideStar,
        class: "stroke-amber-500 fill-amber-500",
        action: (entities) => {
          entities.forEach((e) => (e.is_favourite = false))
          props.getEntities.setData(props.getEntities.data)
          toggleFav.submit({ entities })
        },
        isEnabled: (e) => e.is_favourite && !e.external,
        important: true,
        multi: true,
      },
      {
        label: __("Remove from Recents"),
        icon: LucideClock,
        action: (entities) => {
          clearRecent.submit({
            entities,
          })
        },
        isEnabled: () => route.name == "Recents",
        important: true,
        multi: true,
      },
      { divider: true, isEnabled: (e) => e.write },
      {
        label: __("Delete"),
        icon: LucideTrash,
        action: () => (dialog.value = "remove"),
        isEnabled: (e) => e.write,
        important: true,
        multi: true,
        theme: "red",
      },
    ]
  }
})

const userData = computed(() =>
  allUsers.data ? Object.fromEntries(allUsers.data.map((k) => [k.name, k])) : {}
)

async function newLink() {
  if (!document.hasFocus()) return
  try {
    const text = await navigator.clipboard.readText()
    if (localStorage.getItem("prevClip") === text) return
    localStorage.setItem("prevClip", text)
    const url = new URL(text)
    if (url.host)
      toast({
        title: "Link detected",
        text,
        buttons: [
          {
            label: "Add",
            onClick: () => {
              dialog.value = "l"
            },
          },
        ],
      })
  } catch {}
}

// JS doesn't allow direct reading of clipboard
if (settings.data?.auto_detect_links) {
  newLink()
  window.addEventListener("focus", newLink)
  window.addEventListener("copy", newLink)
}

const socket = inject("socket")
socket.on("list-add", ({ file }) => {
  if (
    file.parent_entity === props.getEntities.params.entity_name &&
    !props.getEntities.data.find((k) => k.name === file.name)
  ) {
    props.getEntities.data.push(...prettyData([file]))
    props.getEntities.setData(props.getEntities.data)
  }
})
socket.on("list-update", ({ file }) => {
  if (file.parent_entity !== props.getEntities.params.entity_name) return
  const index = props.getEntities.data.findIndex((k) => k.name == file.name)
  if (index !== -1)
    props.getEntities.data.splice(index, 1, ...prettyData([file]))
  props.getEntities.setData(props.getEntities.data)
})
socket.on("list-remove", ({ parent, entity_name }) => {
  if (parent !== props.getEntities.params.entity_name) return
  const index = props.getEntities.data.findIndex((k) => k.name == entity_name)
  if (index !== -1) props.getEntities.data.splice(index, 1)
  props.getEntities.setData(props.getEntities.data)
})
socket.on("client-rename", ({ entity_name, title }) => {
  const file = props.getEntities.data.find((k) => k.name === entity_name)
  file.title = title
})
</script>
<style>
.file-drag #drop-area {
  opacity: 0.5;
  padding-left: 0;
  padding-right: 0;
}

.file-drag #drop-area + p {
  display: block;
}
</style>
