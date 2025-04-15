<template>
  <div
    class="h-full w-full px-2 overflow-y-auto flex flex-col"
    @contextmenu="handleContextMenu"
  >
    <DriveToolBar
      v-if="!verify?.error && !getEntities.error"
      :column-headers="$route.name === 'Recents' ? null : columnHeaders"
      :selections
      :entities="rows"
      :action-items="actionItems"
    />

    <FolderContentsError
      v-if="verify?.error || getEntities.error"
      :error="verify?.error || getEntities.error"
    />
    <NoFilesSection
      v-else-if="rows?.length === 0"
      :icon="icon"
      :primary-message="
        activeFilters.length ? 'Nothing found.' : primaryMessage
      "
      :secondary-message="
        activeFilters.length ? 'Try changing filters, maybe?' : secondaryMessage
      "
    />
    <ListView
      v-else
      ref="view"
      v-model="selections"
      :folder-contents="rows && grouper(rows)"
      :action-items="actionItems"
      :entities="rows"
    />
    <Dialogs
      :selections="activeEntity ? [activeEntity] : [...selections]"
      :get-entities="getEntities"
      :handle-list-mutate="handleListMutate"
      v-model="dialog"
    />
    <FileUploader
      v-if="$store.state.auth.user_id"
      @success="getEntities.fetch()"
    />
  </div>
</template>
<script setup>
import ListView from "@/components/ListView.vue"
import GridView from "@/components/GridView.vue"
import DriveToolBar from "@/components/DriveToolBar.vue"
import NoFilesSection from "@/components/NoFilesSection.vue"
import Dialogs from "@/components/Dialogs.vue"
import FolderContentsError from "@/components/FolderContentsError.vue"
import { getLink } from "@/utils/getLink"
import { toggleFav, clearRecent } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { entitiesDownload } from "@/utils/download"
import { RotateCcw } from "lucide-vue-next"
import FileUploader from "@/components/FileUploader.vue"
import Team from "./EspressoIcons/Organization.vue"
import Share from "./EspressoIcons/Share.vue"
import Download from "./EspressoIcons/Download.vue"
import Link from "./EspressoIcons/Link.vue"
import Rename from "./EspressoIcons/Rename.vue"
import Move from "./EspressoIcons/Move.vue"
import Info from "./EspressoIcons/Info.vue"
import Preview from "./EspressoIcons/Preview.vue"
import Trash from "./EspressoIcons/Trash.vue"
import { ref, computed, watch } from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { openEntity } from "@/utils/files"
import { togglePersonal } from "@/resources/files"
import { toast } from "@/utils/toasts"

const props = defineProps({
  grouper: { type: Function, default: (d) => d },
  showSort: { type: Boolean, default: true },
  verify: { Object, default: null },
  icon: Object,
  primaryMessage: String,
  secondaryMessage: { type: String, default: "" },
  getEntities: Object,
})
const route = useRoute()
const store = useStore()

const dialog = ref(null)
const team = route.params.team
const sortOrder = computed(() => store.state.sortOrder)
const activeFilters = computed(() => store.state.activeFilters)
const activeEntity = computed(() => {
  console.log(store.state.activeEntity)
  return store.state.activeEntity
})
const rows = computed(() =>
  props.getEntities.data?.filter?.(
    (k) => k.is_active != 0 && k.title[0] !== "."
  )
)
const selections = ref(new Set())
const fetchEntitites = () => {
  props.getEntities.fetch({
    team,
    order_by: sortOrder.value.ascending
      ? sortOrder.value.field
      : sortOrder.value.field + " desc",
  })
}
watch(sortOrder, fetchEntitites, {
  immediate: route.name !== "Shared" && !props.verify,
})
const verifyAccess = computed(() => props.verify?.data)
watch(verifyAccess, (data) => {
  if (data) fetchEntitites()
})

watch(activeFilters.value, async (val) => {
  props.getEntities.fetch({
    team,
    file_kinds: JSON.stringify(val.map((k) => k.label)),
  })
})

const clickEvent = ref(null)
const defaultContextTriggered = ref(false)
function handleContextMenu(event) {
  clickEvent.value = event
  defaultContextTriggered.value = true
  event.preventDefault()
}
allUsers.fetch({ team })

// Action Items
const actionItems = computed(() => {
  if (route.name === "Trash") {
    return [
      {
        label: "Restore",
        icon: RotateCcw,
        onClick: () => (dialog.value = "restore"),
        multi: true,
        important: true,
      },
      {
        label: "Delete forever",
        icon: Trash,
        onClick: () => (dialog.value = "d"),
        isEnabled: () => route.name === "Trash",
        multi: true,
        important: true,
      },
    ].filter((a) => !a.isEnabled || a.isEnabled())
  } else {
    return [
      {
        label: "Preview",
        icon: Preview,
        onClick: ([entity]) => openEntity(team, entity),
        isEnabled: (e) => !e.is_link,
      },
      {
        label: "Open",
        icon: "external-link",
        onClick: ([entity]) => openEntity(team, entity),
        isEnabled: (e) => e.is_link,
      },
      {
        label: "Download",
        icon: Download,
        isEnabled: (e) => !e.is_link,
        onClick: (entities) => entitiesDownload(team, entities),
        multi: true,
        important: true,
      },
      {
        label: "Share",
        icon: Share,
        onClick: () => (dialog.value = "s"),
        isEnabled: (e) => e.share,
        important: true,
      },
      {
        label: "Get Link",
        icon: Link,
        onClick: ([entity]) => getLink(entity),
        important: true,
      },
      {
        label: "Rename",
        icon: Rename,
        onClick: () => (dialog.value = "rn"),
        isEnabled: (e) => e.write,
      },
      {
        label: "Move",
        icon: Move,
        onClick: () => (dialog.value = "m"),
        isEnabled: (e) => e.write,
        multi: true,
        important: true,
      },
      {
        label: "Move to Team",
        icon: Team,
        onClick: (entities) =>
          confirm(
            `Are you sure you want to move ${entities.length} ${
              entities.length === 1 ? "item" : "items"
            } to the team?`
          ) &&
          entities.map((e) =>
            togglePersonal.submit({ entity_name: e.name, new_value: 0 })
          ),
        isEnabled: () => route.name == "Home",
        multi: true,
        important: true,
      },
      {
        label: "Show Info",
        icon: Info,
        onClick: () => store.commit("setShowInfo", true),
        isEnabled: () => !store.state.activeEntity || !store.state.showInfo,
      },
      {
        label: "Hide Info",
        icon: Info,
        onClick: () => store.commit("setShowInfo", false),
        isEnabled: () => store.state.activeEntity && store.state.showInfo,
      },
      {
        label: "Favourite",
        icon: "star",
        onClick: (entities) => {
          entities = entities.map((e) => ({
            ...e,
            is_favourite: true,
          }))
          toggleFav.submit({ entities })
          entities.map((data) => handleListMutate({ data }))
        },
        isEnabled: (e, multi) => !e.is_favourite,
        important: true,
        multi: true,
      },
      {
        label: "Unfavourite",
        icon: "star",
        class: "stroke-amber-500 fill-amber-500",
        onClick: (entities) => {
          entities = entities.map((e) => ({
            ...e,
            is_favourite: false,
          }))
          toggleFav.submit({ entities })
          entities.map((data) => handleListMutate({ data }))
        },
        isEnabled: (e) => e.is_favourite,
        important: true,
        multi: true,
      },
      {
        label: "Remove from Recents",
        icon: "clock",
        onClick: (entities) => {
          clearRecent.submit({
            entities,
          })
          entities.map((data) => handleListMutate({ data }))
        },
        isEnabled: (e) => e.accessed,
        important: true,
        multi: true,
      },
      {
        label: "Unshare",
        danger: true,
        icon: "trash-2",
        onClick: () => (dialog.value = "unshare"),
        isEnabled: (e) =>
          e.owner != "You" && e.user_doctype === "User" && e.everyone !== 1,
      },
      {
        label: "Move to Trash",
        icon: Trash,
        onClick: () => (dialog.value = "remove"),
        isEnabled: (e) => e.write,
        important: true,
        multi: true,
        danger: true,
      },
    ]
  }
})

function handleListMutate({ data: newData, new: _new, delete: _delete, all }) {
  props.getEntities.setData((data) => {
    if (_new) data.push(newData)
    const index = data.findIndex((o) => o.name === newData.name)
    if (_delete && all) data.splice(0, data.length)
    else if (_delete && !all) data.splice(index, 1)
    else data.splice(index, 1, { ...data[index], ...newData })
    return data
  })
}

const columnHeaders = [
  {
    label: "Name",
    field: "title",
  },
  {
    label: "Owner",
    field: "owner",
  },
  {
    label: "Modified",
    field: "modified",
  },
  {
    label: "Size",
    field: "file_size",
  },
  {
    label: "Type",
    field: "mime_type",
  },
]

async function newLink() {
  if (!document.hasFocus()) return
  try {
    const text = await navigator.clipboard.readText()
    if (localStorage.getItem("prevClip") === text) return
    new URL(text)
    localStorage.setItem("prevClip", text)
    toast({
      title: "Link detected",
      text,
      buttons: [
        {
          label: "Add",
          action: () => {
            dialog.value = "l"
          },
        },
      ],
    })
  } catch (_) {}
}

// Hacky but performant way to track links - when the user loads page, copies on page, or comes to page
// JS doesn't allow direct reading of clipboard
newLink()
addEventListener("copy", () => document.getElementById("popovers").click())
document.getElementById("popovers").addEventListener("click", newLink)
document.addEventListener("visibilitychange", () => {
  window.focus()
  !document.hidden && setTimeout(newLink, 100)
})
</script>
