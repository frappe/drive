<template>
  <FrappeListView
    row-key="name"
    :columns="selectedColumns"
    :rows="formattedRows"
    :options="{
      selectable: true,
      showTooltip: true,
      resizeColumn: true,
    }"
  >
    <ListHeader />
    <Loader v-if="!entities || entities.loading" />
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
            <CustomListRow
              :rows="group.rows"
              :context-menu="contextMenu"
              :set-active="setActive"
              :selected="(row) => selectedRow?.name === row.name"
              :hovered="(row) => hoveredRow === row.name"
              @mouseenter="(row) => (hoveredRow = row.name)"
              @mouseleave="() => (hoveredRow = null)"
            />
          </ListGroupRows>
        </div>
        <div v-else>
          <CustomListRow
            :rows="formattedRows"
            :context-menu="contextMenu"
            :set-active="setActive"
            :selected="(row) => selectedRow?.name === row.name"
            :hovered="(row) => hoveredRow === row.name"
            @mouseenter="(row) => (hoveredRow = row.name)"
            @mouseleave="hoveredRow = null"
          />
        </div>
      </div>
    </template>
    <ListSelectBanner>
      <template #actions="{ selections }">
        <div class="flex gap-3">
          <Button
            v-for="(item, index) in actionItems
              .filter(
                (i) => i.important && ([...selections].length === 1 || i.multi)
              )
              .filter(
                (i) =>
                  !i.isEnabled ||
                  [...selections]
                    .map((n) => entities.find((e) => e.name === n))
                    .every((e) => i.isEnabled(e, [...selections].length !== 1))
              )"
            :key="index"
            @click="
              () =>
                handleAction(
                  [...selections].map((n) =>
                    entities.find((e) => e.name === n)
                  ),
                  item
                )
            "
          >
            <component
              :is="item.icon"
              class="h-4 w-auto text-gray-800"
              :class="item.danger ? 'text-red-500' : ''"
            />
          </Button>
        </div>
      </template>
    </ListSelectBanner>
  </FrappeListView>
  <EmptyEntityContextMenu
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
  Button,
  ListSelectBanner,
  ListHeader,
  ListGroupRows,
  ListGroupHeader,
  ListView as FrappeListView,
  Avatar,
} from "frappe-ui"
import Loader from "@/components/Loader.vue"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import { computed, h, ref } from "vue"
import EmptyEntityContextMenu from "@/components/EmptyEntityContextMenu.vue"
import Folder from "./MimeIcons/Folder.vue"
import { allUsers } from "../resources/permissions"
import CustomListRow from "./CustomListRow.vue"

const store = useStore()
const route = useRoute()
const hoveredRow = ref(null)
const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  entities: Array,
})
const selectedRow = ref(null)
const rowEvent = ref(null)
const userData = computed(() =>
  allUsers.data ? Object.fromEntries(allUsers.data.map((k) => [k.name, k])) : {}
)
const formattedRows = computed(() => {
  if (!props.folderContents) return []
  if (Array.isArray(props.folderContents)) return props.folderContents
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
    getLabel: ({ row: { title, is_group } }) =>
      title.lastIndexOf(".") === -1 || is_group
        ? title
        : title.slice(0, title.lastIndexOf(".")),
    prefix: ({ row }) =>
      row.is_group
        ? h(Folder)
        : h("img", { src: getIconUrl(formatMimeType(row.mime_type)) }),
    width: 2.5,
  },
  {
    label: "Owner",
    key: "",
    getLabel: ({ row }) =>
      row.owner === store.state.auth.userId
        ? "You"
        : userData.value[row.owner]?.full_name || row.owner,
    prefix: ({ row }) => {
      return h(Avatar, {
        shape: "circle",
        image: userData.value[row.owner]?.user_image,
        label: userData.value[row.owner]?.full_name,
        size: "sm",
      })
    },
  },
  {
    label: "Last Modified",
    getLabel: ({ row }) => row.relativeModified,
    key: "modified",
    isEnabled: (n) => n !== "Recents",
  },
  {
    label: "Last Accessed",
    getLabel: ({ row }) => row.relativeAccessed,
    key: "modified",
    isEnabled: (n) => n === "Recents",
  },
  {
    label: "Size",
    key: "",
    getLabel: ({ row }) => row.file_size_pretty,
  },
  { label: "", key: "options", align: "right", width: "10px" },
].filter((k) => !k.isEnabled || k.isEnabled(route.name))

const setActive = (entity) => {
  if (entity.name === store.state.activeEntity?.name) {
    selectedRow.value = null
    store.commit("setActiveEntity", null)
  } else {
    selectedRow.value = entity
    store.commit("setActiveEntity", entity)
  }
}

const handleAction = (selectedItems, action) => {
  selections.value = selectedItems
  action.onClick(selectedItems)
}

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

const selections = defineModel()
const contextMenu = (event, row) => {
  selectedRow.value = row
  rowEvent.value = event
  event.stopPropagation()
  event.preventDefault()
}
</script>
