<template>
  <FrappeListView
    class="px-[10px] pt-3 select-none"
    row-key="name"
    :columns="selectedColumns"
    :rows="formattedRows"
    @update:selections="handleSelections"
    @update:active-row="setActive"
    :options="{
      selectable: true,
      enableActive: true,
      showTooltip: true,
      resizeColumn: false,
      // Should be getLink(row, false, false) - but messes up clicking
      getRowRoute: (row) => '',
      emptyState: {
        description: 'Nothing found with that search - try something else?',
      },
    }"
  >
    <ListHeader>
      <template #default>
        <ListHeaderItem
          v-for="column in selectedColumns"
          :key="column.key"
          :item="column"
        >
          <template v-if="column.key === 'title'" #suffix>
            <div class="absolute right-0 flex gap-0">
              <TextInput
                ref="searchInput"
                v-model="filter"
                type="text"
                class="my-auto scale-[88%]"
                :class="showSearch ? 'opacity-1' : 'opacity-0'"
                placeholder="search..."
              />

              <Button @click=";(showSearch = !showSearch), (filter = '')">
                <LucideSearch v-if="!showSearch" class="my-auto w-3 h-3" />
                <LucideX v-else class="my-auto w-3 h-3" />
              </Button>
            </div>
          </template>
        </ListHeaderItem>
      </template>
    </ListHeader>
    <div
      v-if="!folderContents"
      class="w-full text-center flex items-center justify-center py-10"
    >
      <LoadingIndicator class="w-8" />
    </div>
    <template v-else>
      <div id="drop-area" class="h-full overflow-y-auto">
        <ListEmptyState v-if="!formattedRows.length" />
        <div
          v-else-if="formattedRows[0].group"
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
        <div v-else="formattedRows.length">
          <CustomListRow :rows="formattedRows" :context-menu="contextMenu" />
        </div>
      </div>
      <p class="hidden text-center w-[20%] left-[40%] top-[50%] z-10 font-bold">
        Drop to upload
      </p>
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
  TextInput,
  ListGroupHeader,
  ListEmptyState,
  ListHeaderItem,
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
import CustomListRow from "./CustomListRow.vue"
import { openEntity } from "@/utils/files"
import { formatDate } from "@/utils/format"

const store = useStore()
const route = useRoute()
const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  userData: Object,
})

const selections = defineModel(new Set())
const selectedRow = ref(null)

const rowEvent = ref(null)

const showSearch = ref(false)
const searchInput = ref(null)
const filter = ref("")
watch(showSearch, (v) => {
  if (v) searchInput.value[0].el.focus()
})

const formattedRows = computed(() => {
  if (!props.folderContents) return []
  if (Array.isArray(props.folderContents))
    return props.folderContents.filter((k) => k.title.includes(filter.value))
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
      row.owner === store.state.user.id
        ? "You"
        : props.userData[row.owner]?.full_name || row.owner,
    prefix: ({ row }) => {
      return h(Avatar, {
        shape: "circle",
        image: props.userData[row.owner]?.user_image,
        label:
          props.userData[row.owner]?.full_name ||
          props.userData[row.owner]?.email,
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
    getLabel: ({ row }) =>
      row.is_group
        ? row.children
          ? row.children + " item" + (row.children === 1 ? "" : "s")
          : "empty"
        : row.file_size_pretty,
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
<style>
.dz-drag-hover #drop-area {
  opacity: 0.5;
  border: black 2px dotted;
  box-sizing: content-box;
  padding-left: 0;
  padding-right: 0;
}

.dz-drag-hover #drop-area + p {
  display: block;
  position: absolute;
}
</style>
