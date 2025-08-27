<template>
  <Navbar
    v-if="!verify?.error && !getEntities.error"
    :actions="
      verify?.data &&
      actionItems
        .filter((k) => k.isEnabled?.(verify.data))
        // Remove irrelevant ones
        .slice(1)
        .toSpliced(4, 1)
        .map((k) => ({ ...k, onClick: () => k.action([verify.data]) }))
    "
    :trigger-root="
      () => ((selections = new Set()), store.commit('setActiveEntity', null))
    "
    :root-resource="verify"
    @show-team-members="emit('show-team-members')"
  />

  <ErrorPage
    v-if="verify?.error || getEntities.error"
    :error="verify?.error || getEntities.error"
  />

  <div
    v-else
    ref="container"
    class="flex flex-col overflow-auto min-h-full bg-surface-white"
  >
    <!-- Content Area with Team Members -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Main Content -->
      <div class="flex-1 flex flex-col">
        <DriveToolBar
          v-model="rows"
          :action-items="actionItems"
          :selections="selectedEntitities"
          :get-entities="getEntities"
        />
        <div
          v-if="!props.getEntities.fetched"
          class="m-auto"
          style="transform: translate(0, -88.5px)"
        >
          <LoadingIndicator class="size-10 text-ink-gray-9" />
        </div>
        <NoFilesSection
          v-else-if="!props.getEntities.data?.length"
          :icon="icon"
          :primary-message="__(primaryMessage)"
          :secondary-message="__(secondaryMessage)"
        />
        <ListView
          v-else-if="$store.state.view === 'list'"
          v-model="selections"
          :folder-contents="rows && grouper(rows)"
          :action-items="actionItems"
          :user-data="userData"
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

      <!-- Team Members List - Bỏ ra khỏi GenericPage -->
      <!-- TeamMembersList sẽ được render ở component Team -->
    </div>
    <InfoPopup :entities="infoEntities" />
  </div>

  <Dialogs
    v-model="dialog"
    :selected-rows="activeEntity ? [activeEntity] : selectedEntitities"
    :root-resource="verify"
    :get-entities="getEntities"
  />
  <FileUploader
    v-if="$store.state.user.id"
    @success="getEntities.fetch()"
  />
</template>
<script setup>
import Dialogs from "@/components/Dialogs.vue"
import ErrorPage from "@/components/ErrorPage.vue"
import FileUploader from "@/components/FileUploader.vue"
import GridView from "@/components/GridView.vue"
import InfoPopup from "@/components/InfoPopup.vue"
import ListView from "@/components/ListView.vue"
import Navbar from "@/components/Navbar.vue"
import NoFilesSection from "@/components/NoFilesSection.vue"
import TeamMembersList from "@/components/TeamMembersList.vue"
import { clearRecent, toggleFav } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { entitiesDownload } from "@/utils/download"
import { getLink } from "@/utils/getLink"

import { allFolders, move } from "@/resources/files"
import { settings } from "@/resources/permissions"
import { openEntity } from "@/utils/files"
import { toast } from "@/utils/toasts"
import { LoadingIndicator } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"

import LucideClock from "~icons/lucide/clock"
import LucideDownload from "~icons/lucide/download"
import LucideExternalLink from "~icons/lucide/external-link"
import LucideEye from "~icons/lucide/eye"
import LucideInfo from "~icons/lucide/info"
import LucideLink2 from "~icons/lucide/link-2"
import LucideMoveUpRight from "~icons/lucide/move-up-right"
import LucideRotateCcw from "~icons/lucide/rotate-ccw"
import LucideShare2 from "~icons/lucide/share-2"
import LucideSquarePen from "~icons/lucide/square-pen"
import LucideStar from "~icons/lucide/star"
import LucideTrash from "~icons/lucide/trash"

const props = defineProps({
  grouper: { type: Function, default: (d) => d },
  showSort: { type: Boolean, default: true },
  verify: { Object, default: null },
  icon: [Function, Object],
  primaryMessage: String,
  secondaryMessage: { type: String, default: "" },
  getEntities: Object,
})

// Define emits
const emit = defineEmits(['show-team-members'])

const route = useRoute()
const store = useStore()

const dialog = ref("")
const infoEntities = ref([])
const team = route.params.team
const activeEntity = computed(() => store.state.activeEntity)
const rows = ref(props.getEntities.data)

// Bỏ showTeamMembersList và handleCloseTeamMembers vì sẽ được handle ở component Team

watch(
  () => props.getEntities.data,
  (val) => {
    rows.value = val
  }
)

const selections = ref(new Set())
const selectedEntitities = computed(
  () =>
    props.getEntities.data?.filter?.(({ name }) =>
      selections.value.has(name)
    ) || []
)

const verifyAccess = computed(() => props.verify?.data || !props.verify)

watch(
  verifyAccess,
  async (data) => {
    if (data)
      await props.getEntities.fetch({
        team,
        order_by:
          store.state.sortOrder.field +
          (store.state.sortOrder.ascending ? " 1" : " 0"),
      })
  },
  { immediate: true }
)

if (team) {
  allUsers.fetch({ team })
  allFolders.fetch({ team })
}
if (!settings.fetched) settings.fetch()

// Drag and drop
const onDrop = (targetFile, draggedItem) => {
  if (!targetFile.is_group || draggedItem === targetFile.name || !draggedItem)
    return
  move.submit({
    entity_names: [draggedItem],
    new_parent: targetFile.name,
  })
  const removedIndex = props.getEntities.data.findIndex(
    (k) => k.name === draggedItem
  )
  props.getEntities.data.splice(removedIndex, 1)
  props.getEntities.data.find((k) => k.name === targetFile.name).children += 1
  props.getEntities.setData(data)
}

// Action Items
const actionItems = computed(() => {
  if (route.name === "Trash") {
    return [
      {
        label: "Khôi phục",
        icon: LucideRotateCcw,
        action: () => (dialog.value = "restore"),
        multi: true,
        important: true,
      },
      {
        label: "Xóa vĩnh viễn",
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
        label: "Xem trước",
        icon: LucideEye,
        action: ([entity]) => openEntity(team, entity),
        isEnabled: (e) => !e.is_link,
      },
      {
        label: "Mở",
        icon: LucideExternalLink,
        action: ([entity]) => openEntity(team, entity),
        isEnabled: (e) => e.is_link,
      },
      { divider: true },
      {
        label: "Chia sẻ",
        icon: LucideShare2,
        action: () => (dialog.value = "s"),
        isEnabled: (e) => e.share,
        important: true,
      },
      {
        label: "Tải xuống",
        icon: LucideDownload,
        isEnabled: (e) => !e.is_link,
        action: (entities) => entitiesDownload(team, entities),
        multi: true,
        important: true,
      },
      {
        label: "Sao chép liên kết",
        icon: LucideLink2,
        action: ([entity]) => getLink(entity),
        important: true,
      },
      { divider: true },
      {
        label: "Di chuyển",
        icon: LucideMoveUpRight,
        action: () => (dialog.value = "m"),
        isEnabled: (e) => e.write,
        multi: true,
        important: true,
      },
      {
        label: "Đổi tên",
        icon: LucideSquarePen,
        action: () => (dialog.value = "rn"),
        isEnabled: (e) => e.write,
      },
      {
        label: "Hiển thị thông tin",
        icon: LucideInfo,
        action: () => infoEntities.value.push(store.state.activeEntity),
        isEnabled: () => !store.state.activeEntity || !store.state.showInfo,
      },
      {
        label: "Ẩn thông tin",
        icon: LucideInfo,
        action: () => (dialog.value = "info"),
        isEnabled: () => store.state.activeEntity && store.state.showInfo,
      },
      {
        label: "Yêu thích",
        icon: LucideStar,
        action: (entities) => {
          entities.forEach((e) => (e.is_favourite = true))
          // Hack to cache
          props.getEntities.setData(props.getEntities.data)
          toggleFav.submit({ entities })
        },
        isEnabled: (e) => !e.is_favourite,
        important: true,
        multi: true,
      },
      {
        label: "Bỏ yêu thích",
        icon: LucideStar,
        class: "stroke-amber-500 fill-amber-500",
        action: (entities) => {
          entities.forEach((e) => (e.is_favourite = false))
          props.getEntities.setData(props.getEntities.data)
          toggleFav.submit({ entities })
        },
        isEnabled: (e) => e.is_favourite,
        important: true,
        multi: true,
      },
      {
        label: "Xóa khỏi gần đây",
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
        label: "Xóa",
        icon: LucideTrash,
        action: () => (dialog.value = "remove"),
        isEnabled: (e) => e.write,
        important: true,
        multi: true,
        danger: true,
        color: "text-ink-red-4",
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
    url = new URL(text)
    if (url.host)
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

// JS doesn't allow direct reading of clipboard
if (settings.data?.auto_detect_links) {
  newLink()
  window.addEventListener("focus", newLink)
  window.addEventListener("copy", newLink)
}
</script>