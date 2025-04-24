<template>
  <FrappeListView
    class="px-0.5 select-none"
    row-key="name"
    :columns="selectedColumns"
    :rows="formattedRows"
    @update:selections="handleSelections"
    @update:active-row="setActive"
    :options="{
      selectable: true,
      enableActive: true,
      showTooltip: true,
      resizeColumn: true,
      getRowRoute: (row) => getLink(row, false, false),
    }"
  >
    <ListHeader />
    <div
      v-if="!entities"
      class="w-full text-center flex items-center justify-center py-10"
    >
      <LoadingIndicator class="w-8" />
    </div>
    <template v-else>
      <div class="h-full overflow-y-auto">
        <div
          v-if="formattedRows[0].group"
          v-for="group in formattedRows"
          :key="group.group"
        >
          <ListGroupHeader :group="group">
            <slot
              v-if="$slots['group-header']"
              name="group-header"
              v-bind="{ group }"
            />
          </ListGroupHeader>
          <ListGroupRows :group="group">
            <CustomListRow :rows="group.rows" :context-menu="contextMenu" />
          </ListGroupRows>
        </div>
        <div v-else>
          <CustomListRow :rows="formattedRows" :context-menu="contextMenu" />
        </div>
      </div>
    </template>
  </FrappeListView>
  <ContextMenu
    v-if="rowEvent && selectedRow"
    :key="selectedRow.name"
    v-on-outside-click="() => (rowEvent = false)"
    :close="() => (rowEvent = false)"
    :action-items="dropdownActionItems(selectedRow)"
    :event="rowEvent"
  />
</template>
<script setup>
import {
  ListHeader,
  ListGroupRows,
  ListGroupHeader,
  LoadingIndicator,
  ListView as FrappeListView,
  Avatar,
} from "frappe-ui"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import { computed, h, ref, watch } from "vue"
import ContextMenu from "@/components/ContextMenu.vue"
import Folder from "./MimeIcons/Folder.vue"
import { allUsers } from "@/resources/permissions"
import CustomListRow from "./CustomListRow.vue"
import { openEntity } from "@/utils/files"
import { formatDate } from "@/utils/format"
import { getLink } from "../utils/getLink"

const store = useStore()
const route = useRoute()
const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  entities: Array,
})
const selections = defineModel()
const selectedRow = ref(null)
const rowEvent = ref(null)
const userData = computed(() =>
  allUsers.data ? Object.fromEntries(allUsers.data.map((k) => [k.name, k])) : {}
)
const formattedRows = computed(() => {
  if (!props.folderContents) return []
  if (Array.isArray(props.folderContents))
    return props.folderContents.filter((k) => k)
  return Object.keys(props.folderContents)
    .map((k) => ({
      group: k,
      rows: props.folderContents[k] || [],
      collapsed: false,
    }))
    .filter((g) => g.rows.length)
})

const selectedColumns = [
  {
    label: "Name",
    key: "title",
    getLabel: ({ row: { title, is_group, document } }) =>
      title.lastIndexOf(".") === -1 || is_group || document
        ? title
        : title.slice(0, title.lastIndexOf(".")),
    getTooltip: (e) => (e.is_group || e.document ? "" : e.title),
    prefix: ({ row }) =>
      row.is_group
        ? h(Folder)
        : h("img", { src: getIconUrl(formatMimeType(row.mime_type)) }),
    width: "50%",
  },
  {
    label: "Owner",
    key: "",
    getLabel: ({ row }) =>
      row.owner === store.state.auth.user_id
        ? "You"
        : userData.value[row.owner]?.full_name || row.owner,
    prefix: ({ row }) => {
      return h(Avatar, {
        shape: "circle",
        image: userData.value[row.owner]?.user_image,
        label:
          userData.value[row.owner]?.full_name ||
          userData.value[row.owner]?.email,
        size: "sm",
      })
    },
    width: "20%",
  },
  {
    label: "Last Modified",
    getLabel: ({ row }) => row.relativeModified,
    getTooltip: (row) => formatDate(row.modified),
    key: "modified",
    isEnabled: (n) => n !== "Recents",
    width: "15%",
  },
  {
    label: "Last Accessed",
    getLabel: ({ row }) => row.relativeAccessed,
    getTooltip: (row) => formatDate(row.accessed),
    key: "modified",
    isEnabled: (n) => n === "Recents",
    width: "15%",
  },
  {
    label: "Size",
    key: "",
    getLabel: ({ row }) => row.file_size_pretty, // || "<em>empty</em>",
    width: "10%",
  },
  { label: "", key: "options", align: "right", width: "10px" },
].filter((k) => !k.isEnabled || k.isEnabled(route.name))

const setActive = (entity) => {
  selectedRow.value =
    !entity || entity.name !== store.state.activeEntity?.name ? entity : null
}

watch(selectedRow, (k) => store.commit("setActiveEntity", k))

const dropdownActionItems = (row) => {
  if (!row) return []
  return props.actionItems
    .filter((a) => !a.isEnabled || a.isEnabled(row))
    .map((a) => ({
      ...a,
      handler: () => {
        rowEvent.value = false
        store.commit("setActiveEntity", row)
        a.onClick([row])
      },
    }))
}

const contextMenu = (event, row) => {
  if (selections.value.size > 0) return
  // Ctrl + click triggers context menu on Mac
  if (event.ctrlKey) openEntity(route.params.team, row, true)
  rowEvent.value = event
  selectedRow.value = row
  event.stopPropagation()
  event.preventDefault()
}

const handleSelections = (sels) => {
  selections.value = sels
  selectedRow.value = null
  store.commit("setActiveEntity", null)
}
</script>
