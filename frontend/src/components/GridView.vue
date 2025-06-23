<template>
  <!-- pt-1 to accomodate borders -->
  <div
    v-if="rows?.length"
    class="grid-container gap-5 p-5 pb-[60px] overflow-auto select-none"
  >
    <div
      v-for="file in rows"
      :id="file.name"
      :key="file.name"
      class="grid-item rounded-lg group select-none entity cursor-pointer relative h-[172px] border bg-surface-white"
      :class="[
        selections.has(file.name) || selectedRow?.name === file.name
          ? 'bg-surface-gray-2 shadow-gray'
          : 'border-outline-gray-modals hover:shadow-lg',
        draggedItem === file.name ? 'opacity-60 hover:shadow-none' : '',
      ]"
      :draggable="true"
      @dragstart="draggedItem = file.name"
      @dragend="draggedItem = null"
      @dragover="file.is_group && $event.preventDefault()"
      @drop="$emit('dropped', file, draggedItem)"
      @click.meta="
        selections.has(file.name)
          ? selections.delete(file.name)
          : selections.add(file.name)
      "
      @[action]="open(file)"
      @contextmenu="contextMenu($event, file)"
      @mousedown.stop
    >
      <LucideStar
        v-if="$route.name !== 'Favourites' && file.is_favourite"
        class="stroke-amber-500 fill-amber-500 z-10 absolute top-2 left-2 h-4"
        width="16"
        height="16"
      />
      <Button
        :variant="'subtle'"
        class="z-10 duration-300 absolute top-2 right-2"
        :class="[
          selections.size > 0 ? '' : '!bg-surface-gray-3 hover:shadow-lg',
          selectedRow?.name === file.name
            ? ''
            : 'invisible group-hover:visible',
        ]"
        @click.stop="contextMenu($event, file)"
      >
        <LucideMoreHorizontal class="size-4" />
      </Button>
      <GridItem :file="file" />
    </div>
  </div>
  <ContextMenu
    v-if="rowEvent && selectedRow"
    :key="selectedRow.name"
    v-on-outside-click="() => ((rowEvent = false), (selectedRow = null))"
    :close="() => ((rowEvent = false), (selectedRow = null))"
    :action-items="dropdownActionItems(selectedRow)"
    :event="rowEvent"
  />
</template>

<script setup>
import GridItem from "@/components/GridItem.vue"
import emitter from "@/emitter"
import { Button } from "frappe-ui"
import { ref, computed } from "vue"
import { openEntity } from "@/utils/files"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { settings } from "@/resources/permissions"
import { onKeyDown } from "@vueuse/core"

const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  userData: Object,
})
const emit = defineEmits(["dropped"])
const route = useRoute()
const store = useStore()
const selections = defineModel(new Set())

const rows = computed(() => props.folderContents)
const action = (settings.data.message || settings.data).single_click
  ? "click"
  : "dblclick"

const selectedRow = ref(null)
const rowEvent = ref(null)

// Duplication, redesign
const contextMenu = (event, row) => {
  if (selections.value.size > 0) return
  // Ctrl + click triggers context menu on Mac
  if (event.ctrlKey) openEntity(route.params.team, row, true)
  rowEvent.value = event
  selectedRow.value = row
  event.stopPropagation()
  event.preventDefault()
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
        a.action([row])
      },
    }))
}
const open = (row) =>
  !selections.value.size &&
  route.name !== "Trash" &&
  openEntity(route.params.team, row)

const draggedItem = ref(null)

onKeyDown("a", (e) => {
  if (
    e.target.classList.contains("ProseMirror") ||
    e.target.tagName === "INPUT" ||
    e.target.tagName === "TEXTAREA"
  )
    return
  if (e.metaKey) {
    selections.value = new Set(props.folderContents.map((k) => k.name))
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
  selections.value = new Set()
  e.preventDefault()
})
</script>
<style scoped>
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  grid-auto-columns: minmax(170px, 1fr);
}

.shadow-gray {
  box-shadow: 0px 0px 0px 2px rgb(161, 159, 159);
}
</style>
