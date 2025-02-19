<template>
  <div
    class="h-full w-full pt-3.5 px-4 overflow-y-auto flex flex-col"
    @contextmenu="handleContextMenu"
  >
    <DriveToolBar
      :column-headers="$route.name === 'Recents' ? null : columnHeaders"
      :get-entities="getEntities"
    />

    <!-- This sucks, redo it -->
    <FolderContentsError v-if="getEntities.error" :error="getEntities.error" />
    <NoFilesSection
      v-else-if="getEntities.data?.length === 0"
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
      :icon="icon"
      :primary-message="primaryMessage"
      :secondary-message="
        activeFilters.length ? 'Try changing filters, maybe?' : secondaryMessage
      "
    />
    <ListView
      v-else-if="$store.state.view === 'list'"
      ref="view"
      :folder-contents="getEntities.data && grouper(getEntities.data)"
      :entities="getEntities.data"
      :action-items="actionItems"
      v-model="selections"
      @update-offset="() => (page_offset += page_length)"
    />
    <EmptyEntityContextMenu
      v-if="
        ($route.name === 'My Files' ||
          $route.name === 'Home' ||
          $route.name === 'Folder') &&
        defaultContextTriggered
      "
      v-on-outside-click="() => (defaultContextTriggered = false)"
      :close="() => (defaultContextTriggered = false)"
      :action-items="defaultActionItems"
      :event="clickEvent"
    />
    <NewFolderDialog
      v-if="dialog === 'f'"
      v-model="dialog"
      :parent="$route.params.entityName"
      @success="
        (data) => {
          handleListMutate({ new: true, data })
          resetDialog()
        }
      "
    />
    <RenameDialog
      v-if="dialog === 'rn'"
      v-model="dialog"
      :entity="activeEntity"
      @success="((data) => handleListMutate({ data }), resetDialog())"
    />
    <GeneralDialog
      v-if="dialog === 'remove'"
      v-model="dialog"
      :entities="selections"
      :for="'remove'"
      @success="mutate({ delete: true, data: selections })"
    />
    <GeneralDialog
      v-if="dialog === 'unshare'"
      v-model="dialog"
      :entities="selections"
      :for="'unshare'"
      @success="mutate({ delete: true, data: selections })"
    />
    <GeneralDialog
      v-if="dialog === 'restore'"
      v-model="dialog"
      :entities="selections"
      :for="'restore'"
      @success="mutate({ delete: true, data: selections })"
    />
    <ShareDialog
      v-if="dialog === 's'"
      v-model="dialog"
      :entity-name="activeEntity.name"
    />
    <MoveDialog
      v-if="dialog === 'm'"
      v-model="dialog"
      :entities="selections"
      @success="getEntities.fetch(), resetDialog()"
    />
    <DeleteDialog
      v-if="dialog === 'd'"
      v-model="dialog"
      :entities="activeEntity || getEntities.data"
      @success="
        () => {
          if (activeEntity)
            handleListMutate({
              delete: true,
              data: { name: activeEntity.name },
            })
          else getEntities.setData([])
          dialog = null
        }
      "
    />
    <CTADeleteDialog
      v-if="dialog === 'cta'"
      v-model="dialog"
      @success="
        () => {
          getEntities.setData([])
          handleListMutate({ delete: true, all: true })
          dialog = null
        }
      "
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
import NewFolderDialog from "@/components/NewFolderDialog.vue"
import RenameDialog from "@/components/RenameDialog.vue"
import ShareDialog from "@/components/ShareDialog/ShareDialog.vue"
import GeneralDialog from "@/components/GeneralDialog.vue"
import DeleteDialog from "@/components/DeleteDialog.vue"
import CTADeleteDialog from "@/components/CTADeleteDialog.vue"
import MoveDialog from "../components/MoveDialog.vue"
import FolderContentsError from "@/components/FolderContentsError.vue"
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue"
import { getLink } from "@/utils/getLink"
import { toggleFav, clearRecent } from "@/resources/files"
import { entitiesDownload } from "@/utils/download"
import { RotateCcw } from "lucide-vue-next"
import FileUploader from "@/components/FileUploader.vue"
import NewFolder from "./EspressoIcons/NewFolder.vue"
import Home from "./EspressoIcons/Home.vue"
import FileUpload from "./EspressoIcons/File-upload.vue"
import FolderUpload from "./EspressoIcons/Folder-upload.vue"
import Share from "./EspressoIcons/Share.vue"
import Download from "./EspressoIcons/Download.vue"
import Link from "./EspressoIcons/Link.vue"
import Rename from "./EspressoIcons/Rename.vue"
import Move from "./EspressoIcons/Move.vue"
import Info from "./EspressoIcons/Info.vue"
import Preview from "./EspressoIcons/Preview.vue"
import Trash from "./EspressoIcons/Trash.vue"
import NewFile from "./EspressoIcons/NewFile.vue"
import { ref, computed, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"
import { groupByFolder, openEntity, MIME_LIST_MAP } from "@/utils/files"
import { createDocument, togglePersonal } from "@/resources/files"
import emitter from "@/emitter.js"

const props = defineProps({
  grouper: { type: Function, default: groupByFolder },
  showSort: { type: Boolean, default: true },
  icon: Object,
  primaryMessage: String,
  secondaryMessage: { type: String, default: "" },
  getEntities: Object,
})
const route = useRoute()
const router = useRouter()
const store = useStore()

const dialog = ref(null)
const sortOrder = computed(() => store.state.sortOrder)
const activeFilters = computed(() => store.state.activeFilters)
const activeEntity = computed(() => store.state.activeEntity)
const selections = ref([])
watch(activeEntity, () => (selections.value = [activeEntity.value]))
watch(
  sortOrder,
  () => {
    props.getEntities.fetch({
      team: route.params.team,
      order_by: sortOrder.value.ascending
        ? sortOrder.value.field
        : sortOrder.value.field + " desc",
    })
  },
  { immediate: route.name !== "Shared" }
)
watch(activeFilters.value, async (val) => {
  let mime_type_list = JSON.stringify(
    val.reduce((acc, k) => [...acc, ...(MIME_LIST_MAP[k.label] || [])], [])
  )
  props.getEntities.fetch({ team: route.params.team, mime_type_list })
  if (val.find((k) => k.label === "Folder")) {
    setTimeout(() =>
      props.getEntities.fetch(
        {
          team: route.params.team,
          folders: 1,
        },
        600
      )
    )

    setTimeout(
      () =>
        (props.getEntities.data = [
          ...props.getEntities.previousData,
          ...props.getEntities.data,
        ]),
      1000
    )
  }
})

const clickEvent = ref(null)
const defaultContextTriggered = ref(false)
function handleContextMenu(event) {
  clickEvent.value = event
  defaultContextTriggered.value = true
  event.preventDefault()
}

const newDocument = async () => {
  let data = await createDocument.submit({
    title: "Untitled Document",
    team: route.params.team,
    personal: route.name === "My Files" ? 1 : 0,
    content: null,
    parent: store.state.currentFolderID,
  })
  window.open(
    router.resolve({
      name: "Document",
      params: { team: route.params.team, entityName: data.name },
    }).href
  )
}
// Action Items
const defaultActionItems = computed(() => {
  return [
    {
      label: "Upload File",
      icon: FileUpload,
      handler: () => emitter.emit("uploadFile"),
    },
    {
      label: "Upload Folder",
      icon: FolderUpload,
      handler: () => emitter.emit("uploadFolder"),
    },
    {
      label: "New Folder",
      icon: NewFolder,
      handler: () => (dialog.value = "f"),
    },
    {
      label: "New Document",
      icon: NewFile,
      handler: newDocument,
    },
  ]
})

const actionItems = computed(() => {
  if (route.name === "Trash") {
    return [
      {
        label: "Restore",
        icon: RotateCcw,
        onClick: () => (dialog.value = "restore"),
      },
      {
        label: "Delete forever",
        icon: Trash,
        onClick: () => (dialog.value = "d"),
        isEnabled: () => route.name === "Trash",
      },
    ].filter((a) => !a.isEnabled || a.isEnabled())
  } else {
    return [
      {
        label: "Move to Home",
        icon: Home,
        onClick: ([e]) =>
          togglePersonal.submit({ entity_name: e.name, new_value: 0 }),
        isEnabled: () => route.name == "My Files",
        multi: true,
        important: true,
      },
      {
        label: "Preview",
        icon: Preview,
        onClick: ([entity]) => openEntity(route.params.team, entity),
      },
      {
        label: "Download",
        icon: Download,
        onClick: entitiesDownload,
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
            name: e.name,
            is_favourite: true,
          }))
          toggleFav.submit({ entities })
          entities.map((data) => handleListMutate({ data }))
        },
        isEnabled: (e, multi) => !e.is_favourite || multi,
        important: true,
        multi: true,
      },
      {
        label: "Unfavourite",
        icon: "star",
        onClick: (entities) => {
          entities = entities.map((e) => ({
            name: e.name,
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
        onClick: (entities) =>
          clearRecent.submit({
            entities,
          }),
        isEnabled: () => route.name === "Recents",
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

// emitter handling
emitter.on("showCTADelete", () => (dialog.value = "cta"))
emitter.on("showShareDialog", () => (dialog.value = "s"))

const resetDialog = () => (dialog.value = null)
const mutate = (data) => {
  data.data.map((k) => handleListMutate({ ...data, data: k }))
  resetDialog()
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
</script>
