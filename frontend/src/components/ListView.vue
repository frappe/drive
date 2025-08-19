<template>
  <FrappeListView
    ref="container"
    class="relative select-none p-2 sm:p-5 w-full overflow-hidden"
    row-key="name"
    :columns="selectedColumns"
    :rows="formattedRows"
    :options="{
      selectable: true,
      enableActive: true,
      showTooltip: true,
      resizeColumn: windowWidth > 640,
      getRowRoute: () => '',
      emptyState: {
        description: __('Nothing found - try something else?'),
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
        class="h-full overflow-x-auto overflow-y-auto pb-20 min-w-0 
               -webkit-overflow-scrolling-touch scrollbar-thin 
               scrollbar-thumb-gray-300 scrollbar-track-gray-100"
      >
        <ListEmptyState v-if="!formattedRows.length" />
        <template v-else>
          <!-- Grouped rows -->
          <div
            v-for="group in formattedRows"
            v-if="formattedRows[0]?.group"
            :key="group.group"
            :data-group="group.group"
          >
            <div @click="toggleGroup(group.group)" style="cursor: pointer;">
              <ListGroupHeader :group="group" />
            </div>
            <ListGroupRows v-if="!group.collapsed" :group="group">
              <CustomListRow
                :rows="group.rows"
                :context-menu="contextMenu"
                @dropped="(...p) => emit('dropped', ...p)"
              />
            </ListGroupRows>
          </div>

          <!-- Ungrouped rows -->
          <div v-else :key="'ungrouped-rows'">
            <CustomListRow
              :rows="formattedRows"
              :context-menu="contextMenu"
              @dropped="(...p) => emit('dropped', ...p)"
            />
          </div>
        </template>
      </div>

      <p class="hidden absolute text-center w-full top-[50%] z-10 font-bold">
        {{ __('Drop to upload') }}
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
import { computed, h, ref, watch, useTemplateRef, nextTick, onMounted, onUnmounted } from "vue"
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
const collapsedGroups = ref({}) // Track collapsed state of each group
const windowWidth = ref(window.innerWidth)

const rowEvent = ref(null)

// Handle window resize
const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const formattedRows = computed(() => {
  if (!props.folderContents) return []
  if (Array.isArray(props.folderContents)) return props.folderContents
  return Object.keys(props.folderContents)
    .map((k) => ({
      group: k,
      rows: props.folderContents[k] || [],
      collapsed: !!collapsedGroups.value[k],
    }))
    .filter((g) => g.rows.length)
})

// Function to toggle group collapse state
const toggleGroup = async (groupName) => {
  collapsedGroups.value[groupName] = !collapsedGroups.value[groupName]
  
  // Wait for DOM update
  await nextTick()
  
  // Scroll to the group header
  const dropArea = document.getElementById("drop-area")
  if (dropArea) {
    const groupHeader = dropArea.querySelector(`[data-group="${groupName}"]`)
    if (groupHeader) {
      groupHeader.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest',
        inline: 'nearest'
      })
    }
  }
}

const selectedColumns = computed(() => {
  const isMobile = windowWidth.value <= 640
  const isTablet = windowWidth.value <= 768
  const isLaptop = windowWidth.value <= 1024
  
  return [
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
      width: isMobile ? "50%" : isTablet ? "40%" : isLaptop ? "35%" : "30%",
      
      resizable: !isMobile,
    },

    {
      label: __("Owner"),
      key: "",
      getLabel: ({ row }) =>
        row.owner === store.state.user.id
          ? __("You")
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
      width: isMobile ? "0%" : isTablet ? "20%" : "15%",
      
      isEnabled: (n) => !isMobile,
      resizable: !isTablet,
    },
    {
      label: __("Shared"),
      key: "",
      getLabel: ({ row }) => {
        if (row.share_count === -2) return __("Public")
        else if (row.share_count === -1) return __("Team")
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
      width: isMobile ? "0%" : isTablet ? "15%" : "12%",
      
      isEnabled: (n) => !isMobile,
      resizable: !isTablet,
    },
    {
      label: __("Last Modified"),
      getLabel: ({ row }) => row.relativeModified,
      getTooltip: (row) => formatDate(row.creation),
      key: "modified",
      isEnabled: (n) => n !== "Recents" && !isLaptop,
      width: "18%",
      
      resizable: true,
    },
    {
      label: __("Last Accessed"),
      getLabel: ({ row }) => row.relativeAccessed,
      getTooltip: (row) => formatDate(row.accessed),
      key: "modified",
      isEnabled: (n) => n === "Recents" && !isLaptop,
      width: "18%",
      
      resizable: true,
    },
    {
      label: __("Size"),
      key: "",
      getLabel: ({ row }) =>
        row.is_group
          ? row.children
            ? row.children + " " + (row.children === 1 ? __("item") : __("items"))
            : __("empty")
          : row.file_size_pretty,
      width: isMobile ? "0%" : isTablet ? "25%" : isLaptop ? "15%" : "10%",
      resizable: !isMobile,
    },
    { 
      label: "", 
      key: "options", 
      align: "right", 
      width: isMobile ? "40px" : "5%",
      
      resizable: false,
    },
  ].filter((k) => !k.isEnabled || k.isEnabled(route.name))
})

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

/* Smooth scrolling for drop area */
#drop-area {
  scroll-behavior: smooth;
}

/* Group header styling */
[data-group] {
  transition: all 0.2s ease-in-out;
}

/* Responsive table styles */
@media (max-width: 1024px) {
  .frappe-list-view {
    font-size: 14px;
  }
  
  .frappe-list-view .table-header-cell {
    padding: 8px 4px;
  }
  
  .frappe-list-view .list-row {
    padding: 8px 4px;
  }
}

@media (max-width: 768px) {
  .frappe-list-view {
    min-width: 100%;
    font-size: 13px;
  }
  
  .frappe-list-view .table-header-cell {
    padding: 6px 2px;
    font-size: 12px;
  }
  
  .frappe-list-view .list-row {
    padding: 6px 2px;
  }
  
  .frappe-list-view .list-row-content {
    min-height: 44px; /* Touch-friendly height */
  }
}

@media (max-width: 640px) {
  .frappe-list-view {
    font-size: 12px;
  }
  
  .frappe-list-view .table-header-cell {
    padding: 4px 1px;
    font-size: 11px;
  }
  
  .frappe-list-view .list-row {
    padding: 4px 1px;
  }
  
  /* Make name column more prominent on mobile */
  .frappe-list-view .list-row-content .name-column {
    font-weight: 500;
  }
}

/* Ensure table content is scrollable horizontally on small screens */
.frappe-list-view {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: rgba(155, 155, 155, 0.5) transparent;
}

.frappe-list-view::-webkit-scrollbar {
  height: 6px;
}

.frappe-list-view::-webkit-scrollbar-track {
  background: transparent;
}

.frappe-list-view::-webkit-scrollbar-thumb {
  background-color: rgba(155, 155, 155, 0.5);
  border-radius: 20px;
}

.frappe-list-view::-webkit-scrollbar-thumb:hover {
  background-color: rgba(155, 155, 155, 0.7);
}

.frappe-list-view table {
  min-width: 600px;
  table-layout: auto; /* Allow flexible column sizing */
  width: 100%;
}

.frappe-list-view th,
.frappe-list-view td {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Column resizing indicators */
.frappe-list-view .column-resizer {
  cursor: col-resize;
  background: rgba(59, 130, 246, 0.1);
  transition: background 0.2s ease;
}

.frappe-list-view .column-resizer:hover {
  background: rgba(59, 130, 246, 0.2);
}

/* Responsive breakpoints */
@media (max-width: 1024px) {
  .frappe-list-view table {
    min-width: 500px;
  }
}

@media (max-width: 768px) {
  .frappe-list-view table {
    min-width: 400px;
  }
  
  .frappe-list-view .list-row {
    min-height: 48px;
  }
  
  .frappe-list-view .checkbox {
    transform: scale(1.2);
  }
  
  #drop-area::-webkit-scrollbar {
    display: none;
  }
  
  #drop-area {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
}

@media (max-width: 640px) {
  .frappe-list-view table {
    min-width: 320px;
  }
  
  /* Make text more compact on mobile */
  .frappe-list-view .list-row-content {
    font-size: 0.875rem;
    max-width: 150px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  /* Smaller avatars on mobile */
  .frappe-list-view .avatar {
    width: 24px !important;
    height: 24px !important;
  }
  
  /* Optimize button sizes for touch */
  .frappe-list-view .list-row .btn,
  .frappe-list-view .list-row button {
    min-height: 44px;
    min-width: 44px;
  }
}
</style>
