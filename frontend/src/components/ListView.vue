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
      <div v-for="group in formattedRows" :key="group.group">
        <ListGroupHeader :group="group">
          <slot
            v-if="$slots['group-header']"
            name="group-header"
            v-bind="{ group }"
          />
        </ListGroupHeader>
        <ListGroupRows :group="group">
          <template v-for="row in group.rows" :key="row.name">
            <ListRow
              :class="selectedRow === row.name ? '!bg-surface-gray-2' : ''"
              :row="row"
              class="hover:bg-surface-menu-bar"
              @click="setActive(row)"
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
                    <div class="grow justify-items-end">
                      <FeatherIcon
                        v-if="row.is_favourite && route.name !== 'Favourites'"
                        name="star"
                        width="16"
                        height="16"
                        class="stroke-amber-500 fill-amber-500"
                      />
                      <MyDrive
                        v-else-if="
                          row.is_private &&
                          store.state.breadcrumbs[0].label != 'My Space'
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
                    <Dropdown :options="dropdownActionItems(row)">
                      <Button class="bg-white">
                        <FeatherIcon name="more-horizontal" class="h-4 w-4" />
                      </Button>
                    </Dropdown>
                  </template>
                </ListRowItem>
              </template>
            </ListRow>
          </template>
        </ListGroupRows>
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
            <FeatherIcon
              v-if="typeof item.icon === 'string'"
              :name="item.icon"
              class="h-4 w-4"
              :class="
                item.label === 'Unfavourite'
                  ? 'stroke-yellow-500 fill-yellow-500'
                  : ''
              "
            />
            <component
              :is="item.icon"
              v-else
              class="h-4 w-auto text-gray-800"
              :class="item.danger ? 'text-red-500' : ''"
            />
          </Button>
        </div>
      </template>
    </ListSelectBanner>
  </FrappeListView>
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
  Dropdown,
} from "frappe-ui"
import Loader from "@/components/Loader.vue"
import { formatMimeType } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import { computed, h, ref } from "vue"
import Folder from "./MimeIcons/Folder.vue"
import MyDrive from "./EspressoIcons/MyDrive.vue"
import { openEntity } from "@/utils/files"

const store = useStore()
const route = useRoute()
const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  entities: Array,
})
const selectedRow = ref(null)
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
    getLabel: ({ row: { title } }) =>
      title.lastIndexOf(".") === -1
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
    getLabel: ({ row }) => row.owner,
    // prefix: ({ row }) =>
    //   h(Avatar, {
    //     shape: "circle",
    //     image: row.user_image,
    //     label: row.full_name,
    //     size: "sm",
    //   }),
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
    selectedRow.value = entity.name
    store.commit("setActiveEntity", entity)
  }
}

const handleAction = (selectedItems, action) => {
  selections.value = selectedItems
  action.onClick(selectedItems)
}

const dropdownActionItems = (row) => {
  return props.actionItems
    .filter((a) => !a.isEnabled || a.isEnabled(row))
    .map((a) => ({
      ...a,
      onClick: () => {
        selectedRow.value = row.name
        store.commit("setActiveEntity", row)
        a.onClick([row])
      },
    }))
}

const selections = defineModel()
</script>
