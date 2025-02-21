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
        <div v-for="group in formattedRows" :key="group.group">
          <ListGroupHeader :group="group">
            <slot
              v-if="$slots['group-header']"
              name="group-header"
              v-bind="{ group }"
            />
          </ListGroupHeader>
          <ListGroupRows :group="group">
            <ListRow
              v-for="row in group.rows"
              :class="
                selectedRow?.name === row.name ? '!bg-surface-gray-2' : ''
              "
              :key="row.name"
              :row="row"
              class="hover:bg-surface-menu-bar cursor-pointer"
              @click="setActive(row)"
              @mouseenter="hoveredRow = row.name"
              @mouseexit="hoveredRow = null"
              @contextmenu="(e) => contextMenu(e, row)"
              @dblclick="() => openEntity(route.params.team, row)"
            >
              <template #default="{ idx, column, item }">
                <ListRowItem
                  :column="column"
                  :row="row"
                  :item="item"
                  :align="column.align"
                >
                  <template v-if="idx === 0" #suffix>
                    <div class="flex flex-row grow justify-end gap-2">
                      <div v-if="hoveredRow === row.name">
                        <FeatherIcon
                          name="link"
                          class="stroke-1.5 w-4 h-4"
                          @click="getLink(row)"
                        />
                      </div>
                      <FeatherIcon
                        v-if="row.is_favourite && route.name !== 'Favourites'"
                        name="star"
                        width="16"
                        height="16"
                        class="stroke-amber-500 fill-amber-500"
                      />
                      <Lock
                        v-else-if="
                          row.is_private &&
                          store.state.breadcrumbs[0].label != 'My Files'
                        "
                        width="16"
                        height="16"
                      />
                      <FeatherIcon
                        v-else-if="row.accessed && route.name !== 'Recents'"
                        name="clock"
                        width="16"
                        height="16"
                      />
                    </div>
                  </template>
                  <template v-if="column.key === 'options'">
                    <Button
                      class="bg-white me-3"
                      @click="(e) => contextMenu(e, row)"
                    >
                      <FeatherIcon name="more-horizontal" class="h-4 w-4" />
                    </Button>
                  </template>
                </ListRowItem>
              </template>
            </ListRow>
          </ListGroupRows>
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
    :action-items="dropdownActionItems(selectedRow)"
    :event="rowEvent"
  />
</template>
<script setup>
import {
  Button,
  FeatherIcon,
  ListSelectBanner,
  ListHeader,
  ListRowItem,
  ListGroupRows,
  ListRow,
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
import Lock from "./EspressoIcons/Lock.vue"
import { openEntity } from "@/utils/files"
import { allUsers } from "../resources/permissions"
import { getLink } from "../utils/getLink"

const store = useStore()
const route = useRoute()
const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  entities: Array,
})
const selectedRow = ref(null)
const hoveredRow = ref(null)
const rowEvent = ref(null)
const userData = computed(() =>
  allUsers.data ? Object.fromEntries(allUsers.data.map((k) => [k.name, k])) : {}
)
const formattedRows = computed(() => {
  if (!props.folderContents) return []
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
