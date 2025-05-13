<template>
  <div
    v-if="rows?.length"
    class="grid-container px-[10px] py-3 overflow-scroll"
  >
    <div
      v-for="file in rows"
      :id="file.name"
      :key="file.name"
      class="grid-item rounded-lg group select-none entity cursor-pointer relative sm:w-[172px] sm:h-[172px] border"
      :class="[
        selections.has(file.name) || selectedRow?.name === file.name
          ? 'bg-gray-100 shadow-gray'
          : 'border-gray-200 hover:shadow-xl',
      ]"
      :draggable="true"
      @click.meta="
        selections.has(file.name)
          ? selections.delete(file.name)
          : selections.add(file.name)
      "
      @[action]="open(file)"
      @contextmenu="contextMenu($event, file)"
      @mousedown.stop
    >
      <FeatherIcon
        v-if="file.is_favourite"
        class="stroke-amber-500 fill-amber-500 z-10 absolute top-2 left-2 h-4"
        name="star"
        width="16"
        height="16"
      />
      <Button
        :variant="'subtle'"
        @click.stop="contextMenu($event, file)"
        class="z-10 duration-300 absolute invisible top-2 right-2"
        :class="[
          selections.size > 0
            ? ''
            : '!bg-gray-300 hover:bg-gray-400 group-hover:visible',
        ]"
      >
        <FeatherIcon class="h-4" name="more-horizontal" />
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
import { FeatherIcon, Button } from "frappe-ui"
import { ref, computed } from "vue"
import { openEntity } from "@/utils/files"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { settings } from "@/resources/permissions"

const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  userData: Object,
})
const route = useRoute()
const store = useStore()
const selections = defineModel(Set)

const rows = computed(() => props.folderContents)
const action = (settings.data.message || settings.data).single_click
  ? "click"
  : "dblclick"

defineEmits([
  "entitySelected",
  "openEntity",
  "showEntityContext",
  "showEmptyEntityContext",
  "fetchFolderContents",
  "updateOffset",
])

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
        a.onClick([row])
      },
    }))
}
const open = (row) =>
  !selections.value.size &&
  route.name !== "Trash" &&
  openEntity(route.params.team, row)
</script>
<style scoped>
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, 172px);
  gap: 20px;
}

.shadow-gray {
  box-shadow: 0px 0px 0px 2px rgb(161, 159, 159);
}
</style>
