<template>
  <FrappeListView
    ref="container"
    class="relative select-none p-5"
    row-key="name"
    :columns="selectedColumns"
    :rows="formattedRows"
    :options="{
      selectable: true,
      enableActive: true,
      showTooltip: true,
      resizeColumn: false,
      // Should be getLink(row, false, false) - but messes up clicking
      getRowRoute: () => '',
      emptyState: {
        description: 'Nothing found - try something else?',
      },
    }"
    @update:selections="handleSelections"
    @update:active-row="setActive"
  >
    <ListHeader class="mb-[1px]" />
    <div
      v-if="!folderContents"
      class="w-full text-center flex items-center justify-center py-10"
    >
      <LoadingIndicator class="w-8" />
    </div>
    <template v-else>
      <div
        id="drop-area"
        class="h-full overflow-y-auto"
      >
        <ListEmptyState v-if="!formattedRows.length" />
        <div
          v-for="group in formattedRows"
          v-else-if="formattedRows[0].group"
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
              @dropped="emit('dropped')"
            />
          </ListGroupRows>
        </div>
        <div v-else="formattedRows.length">
          <CustomListRow
            :rows="formattedRows"
            :context-menu="contextMenu"
            @dropped="(...p) => $emit('dropped', ...p)"
          />
        </div>
      </div>
      <p class="hidden absolute text-center w-full top-[50%] z-10 font-bold">
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
  ListGroupHeader,
  ListEmptyState,
  LoadingIndicator,
  ListView as FrappeListView,
  Avatar,
} from "frappe-ui"
import { getThumbnailUrl } from "@/utils/getIconUrl"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import { computed, h, ref, watch, useTemplateRef } from "vue"
import ContextMenu from "@/components/ContextMenu.vue"
import CustomListRow from "./CustomListRow.vue"
import { openEntity } from "@/utils/files"
import { formatDate } from "@/utils/format"

import { onKeyDown } from "@vueuse/core"
import emitter from "@/emitter"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideUsers from "~icons/lucide/users"
import LucideGlobe2 from "~icons/lucide/globe-2"

const store = useStore()
const route = useRoute()
const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  userData: Object,
})
const emit = defineEmits(["dropped"])

const container = useTemplateRef("container")
const selections = defineModel(new Set())
const selectedRow = ref(null)

const rowEvent = ref(null)

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
    label: __("Name"),
    key: "title",
    getLabel: ({ row: { title, is_group, document } }) =>
      title.lastIndexOf(".") === -1 || is_group || document
        ? title
        : title.slice(0, title.lastIndexOf(".")),
    getTooltip: (e) => (e.is_group || e.document ? "" : e.title),
    prefix: ({ row }) => {
      return getThumbnailUrl(row.name, row.file_type)
    },
    width: "50%",
  },

  {
    label: __("Owner"),
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
          props.userData[row.owner]?.email ||
          row.owner,
        size: "sm",
      })
    },
    width: "10%",
  },
  {
    label: __("Shared"),
    key: "",
    getLabel: ({ row }) => {
      if (row.share_count === -2) return "Public"
      else if (row.share_count === -1) return "Team"
      else if (row.share_count > 0)
        return (
          row.share_count +
          " " +
          (row.share_count === 1 ? __("person") : __("people"))
        )
      return "-"
    },
    prefix: ({ row }) => {
      if (row.share_count === -2) return h(LucideGlobe2, { class: "size-4" })
      else if (row.share_count === -1)
        return h(LucideBuilding2, { class: "size-4" })
      else if (row.share_count > 0) return h(LucideUsers, { class: "size-4" })
    },
    width: "10%",
  },
  {
    label: __("Last Modified"),
    getLabel: ({ row }) => row.relativeModified,
    getTooltip: (row) => formatDate(row.modified),
    key: "modified",
    isEnabled: (n) => n !== "Recents",
    width: "15%",
  },
  {
    label: __("Last Accessed"),
    getLabel: ({ row }) => row.relativeAccessed,
    getTooltip: (row) => formatDate(row.accessed),
    key: "modified",
    isEnabled: (n) => n === "Recents",
    width: "15%",
  },
  {
    label: __("Size"),
    key: "",
    getLabel: ({ row }) =>
      row.is_group
        ? row.children
          ? row.children + " item" + (row.children === 1 ? "" : "s")
          : "empty"
        : row.file_size_pretty,
    width: "8%",
  },
  { label: "", key: "options", align: "right", width: "5%" },
].filter((k) => !k.isEnabled || k.isEnabled(route.name))

const setActive = (entityName) => {
  const entity = props.folderContents.find((k) => k.name === entityName)
  selectedRow.value =
    !entity || entity.name !== store.state.activeEntity?.name ? entity : null
}

watch(selectedRow, (k) => {
  store.commit("setActiveEntity", k)
})
const dropdownActionItems = (row) => {
  if (!row) return []
  return props.actionItems
    .filter((a) => !a.isEnabled || a.isEnabled(row))
    .map((a) => ({
      ...a,
      handler: () => {
        rowEvent.value = false
        store.commit("setActiveEntity", row)
        a.action([row])
      },
    }))
}

const contextMenu = (event, row) => {
  if (selections.value.size > 0) return
  // Ctrl + click triggers context menu on Mac
  if (event.ctrlKey) openEntity(route.params.team, row, true)
  rowEvent.value = event
  selectedRow.value = row
  console.log(selectedRow.value)
  event.stopPropagation()
  event.preventDefault()
}

const handleSelections = (sels) => {
  selections.value = sels
  selectedRow.value = null
  store.commit("setActiveEntity", null)
}

// Add keyboard shortcuts here as f-ui selections has to be mutated
onKeyDown("a", (e) => {
  // How do I do this nicely?
  if (
    e.target.classList.contains("ProseMirror") ||
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA"
  )
    return
  if (e.metaKey) {
    container.value.selections.clear()
    props.folderContents.map((k) => container.value.selections.add(k.name))
    e.preventDefault()
  }
})
onKeyDown("Backspace", (e) => {
  if (
    e.target.classList.contains("ProseMirror") ||
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA"
  )
    return
  if (e.metaKey) emitter.emit("remove")
})
onKeyDown("m", (e) => {
  if (
    e.target.classList.contains("ProseMirror") ||
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA"
  )
    return
  if (e.ctrlKey) emitter.emit("move")
})
onKeyDown("Escape", (e) => {
  if (
    e.target.classList.contains("ProseMirror") ||
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA"
  )
    return
  container.value.selections.clear()
  e.preventDefault()
})
</script>
<style>
.dz-drag-hover #drop-area {
  opacity: 0.5;
  padding-left: 0;
  padding-right: 0;
}

.dz-drag-hover #drop-area + p {
  display: block;
}
</style>
