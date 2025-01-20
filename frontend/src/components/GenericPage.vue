<template>
  <div
    class="h-full w-full pt-3.5 px-4 pb-5 overflow-y-auto flex flex-col"
    @contextmenu="handleContextMenu"
  >
    <!-- <DriveToolBar :column-headers="showSort ? columnHeaders : null" /> -->
    <DriveToolBar :column-headers="null" />

    <!-- This sucks, redo it -->
    <FolderContentsError v-if="getEntities.error" :error="getEntities.error" />
    <NoFilesSection
      v-else-if="getEntities.data?.length === 0"
      class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
      :icon="icon"
      :primary-message="primaryMessage"
      :secondary-message="secondaryMessage"
    />
    <ListView
      ref="view"
      v-else-if="$store.state.view === 'list'"
      :folder-contents="getEntities.data && grouper(getEntities.data)"
      :entities="getEntities.data"
      :override-can-load-more="overrideCanLoadMore"
      :action-items="actionItems"
      @update-offset="() => (page_offset += page_length)"
    />
    <EmptyEntityContextMenu
      v-if="$route.name === 'Home' && defaultContextTriggered"
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
          // Will break if more folders exist than the pagelength
          // Need to check the sort and see where the newly created folder fits
          // And re-fetch that offset
          handleListMutate({ new: true, data: data })
          dialog = null
        }
      "
    />
    <RenameDialog
      v-if="dialog === 'rn'"
      v-model="dialog"
      :entity="activeEntity"
      @success="
        (data) => {
          handleListMutate({ data })
          dialog = null
        }
      "
    />
    <!-- BROKEN - multiple allowing? -->
    <GeneralDialog
      v-if="dialog === 'remove'"
      v-model="dialog"
      :entities="[activeEntity]"
      :for="'remove'"
      @success="
        () => {
          handleListMutate({ delete: true, data: { name: activeEntity.name } })
          dialog = null
        }
      "
    />
    <GeneralDialog
      v-if="dialog === 'unshare'"
      v-model="dialog"
      :entities="[activeEntity]"
      :for="'unshare'"
      @success="
        () => {
          handleListMutation()
          dialog = null
        }
      "
    />
    <GeneralDialog
      v-if="dialog === 'restore'"
      v-model="dialog"
      :entities="[activeEntity]"
      :for="'restore'"
      @success="
        () => {
          handleListMutate({ delete: true, data: { name: activeEntity.name } })
          dialog = null
        }
      "
    />
    <ShareDialog
      v-if="dialog === 's'"
      v-model="dialog"
      :entity-name="activeEntity.name"
    />
    <MoveDialog
      v-if="dialog === 'm'"
      v-model="dialog"
      :entity="activeEntity"
      @success="
        () => {
          handleListMutate({ delete: true, data: { name: activeEntity.name } })
          dialog = null
        }
      "
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
      :clear-all="clearAll"
      @success="
        () => {
          offset = 0
          folderItems = null
          fetchNextPage()
          handleListMutatation()
          dialog = null
        }
      "
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
import EntityContextMenu from "@/components/EntityContextMenu.vue"
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue"
import { formatSize, formatDate } from "@/utils/format"
import { getLink } from "@/utils/getLink"
import { useTimeAgo } from "@vueuse/core"
import { toggleFav, clearRecent } from "@/resources/files"
import { entitiesDownload } from "@/utils/download"
import { RotateCcw } from "lucide-vue-next"
import NewFolder from "./EspressoIcons/NewFolder.vue"
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
import { toast } from "../utils/toasts.js"
import { capture } from "@/telemetry"
import { calculateRectangle, handleDragSelect } from "@/utils/dragSelect"
import { ref, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from "vuex"
import { groupByFolder } from "@/utils/files"
import emitter from "@/event-bus.js"

const props = defineProps({
  url: String,
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
const clearAll = ref(false)
const activeEntity = computed(() => store.state.activeEntity)

const page_offset = ref(0)
const entity_name = ref("")
const page_length = 1
const DEFAULT_PARAMS = computed(() => ({
  entity_name,
  page_length,
  page_offset,
}))

props.getEntities.update({
  params: DEFAULT_PARAMS.value,
})
props.getEntities.fetch()

const clickEvent = ref(null)
const defaultContextTriggered = ref(false)
function handleContextMenu(event) {
  clickEvent.value = event
  defaultContextTriggered.value = true
  event.preventDefault()
}

function openEntity(entity) {
  if (entity.is_group) {
    router.push({
      name: "Folder",
      params: { entityName: entity.name },
    })
  } else if (entity.mime_type === "frappe_doc") {
    if (store.state.editorNewTab) {
      window.open(
        router.resolve({
          name: "Document",
          params: { entityName: entity.name },
        }).href,
        "_blank"
      )
    } else {
      router.push({
        name: "Document",
        params: { entityName: entity.name },
      })
    }
  } else if (entity.mime_type === "frappe_whiteboard") {
    router.push({
      name: "Whiteboard",
      params: { entityName: entity.name },
    })
  } else {
    router.push({
      name: "File",
      params: { entityName: entity.name },
    })
  }
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
      // BROKEN
      handler: () => this.newDocument(),
    },
    {
      label: "New Whiteboard",
      icon: NewFile,
      // BROKEN
      handler: () => this.newWhiteboard(),
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
        label: "Preview",
        icon: Preview,
        onClick: ([entity]) => openEntity(entity),
        important: true,
      },
      {
        label: "Download",
        icon: Download,
        onClick: entitiesDownload,
        isEnabled: (e) =>
          e.allow_download || e.owner === "You" || e.owner.label === "You",
        multi: true,
        important: true,
      },
      {
        label: "Share",
        icon: Share,
        onClick: () => (dialog.value = "s"),
        isEnabled: (e) =>
          e.owner === "You" || e.owner.label === "You" || e.share,
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
        isEnabled: (e) =>
          e.write || e.owner === "You" || e.owner.label === "You",
      },
      {
        label: "Move",
        icon: Move,
        onClick: () => (dialog.value = "m"),
        isEnabled: (e) => e.owner === "You" || e.owner.label === "You",
        multi: true,
      },
      {
        label: "Show Info",
        icon: Info,
        onClick: () => store.commit("setShowInfo", true),
        isEnabled: () => !store.state.showInfo,
        important: true,
      },
      {
        label: "Hide Info",
        icon: Info,
        onClick: () => store.commit("setShowInfo", false),
        isEnabled: () => store.state.showInfo,
        important: true,
      },
      {
        label: "Favourite",
        icon: "star",
        onClick: (entities) =>
          toggleFav.submit({
            entities: entities.map((e) => ({
              name: e.name,
              is_favourite: true,
            })),
          }),
        isEnabled: (e, multi) => !e.is_favourite || multi,
        important: true,
        multi: true,
      },
      {
        label: "Unfavourite",
        icon: "star",
        onClick: (entities) =>
          toggleFav.submit({
            entities: entities.map((e) => ({
              name: e.name,
              is_favourite: false,
            })),
          }),
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
        isEnabled: (e) => e.owner === "You" || e.owner.label === "You",
        important: true,
        multi: true,
      },
    ]
  }
})

function handleListMutate({ data: newData, new: _new, delete: _delete }) {
  props.getEntities.setData((data) => {
    if (_new) data.push(newData)
    const index = data.findIndex((o) => o.name === newData.name)
    if (_delete) data.splice(index, 1)
    else data.splice(index, 1, { ...data[index], ...newData })
    return data
  })
}
// emitter handling
emitter.on("showCTADelete", () => {
  clearAll.value = true
  dialog.value = "cta"
})
emitter.on("showShareDialog", () => (dialog.value = "s"))
</script>
