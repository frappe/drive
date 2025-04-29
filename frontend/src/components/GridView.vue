<template>
  <div v-if="folderContents.length" class="grid-container px-[10px] pt-3">
    <div
      v-for="file in folderContents"
      :id="file.name"
      :key="file.name"
      class="rounded-lg border group select-none entity cursor-pointer relative sm:w-[182px] sm:h-[182px]"
      :class="[
        selections.includes(file)
          ? 'bg-gray-100 border-gray-300'
          : 'border-gray-200 hover:shadow-xl',
      ]"
      draggable="false"
      @click="open(file)"
      @mousedown.stop
      @contextmenu="contextMenu($event, file)"
    >
      <Button
        :variant="'subtle'"
        :model-value="selections.includes(file)"
        @click.stop="contextMenu($event, file)"
        class="z-10 duration-300 absolute visible group-hover:visible sm:invisible top-2 right-2"
        :class="[
          selections.includes(file)
            ? 'visible '
            : 'sm:bg-gray-300 hover:bg-gray-400  visible sm:invisible',
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
    v-on-outside-click="() => (rowEvent = false)"
    :close="() => (rowEvent = false)"
    :action-items="dropdownActionItems(selectedRow)"
    :event="rowEvent"
  />
</template>

<script setup>
import GridItem from "@/components/GridItem.vue"
import { FeatherIcon, Button } from "frappe-ui"
import { ref, reactive } from "vue"
import { openEntity } from "@/utils/files"
import { useRoute } from "vue-router"
import { useStore } from "vuex"

const props = defineProps({
  folderContents: Object,
  actionItems: Array,
  userData: Object,
})
const route = useRoute()
const store = useStore()
const selections = reactive([])

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
  // if (selections.value.size > 0) return
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
  route.name !== "Trash" && openEntity(route.params.team, row)
</script>
<style scoped>
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(182px, 1fr));
  gap: 20px;
}
</style>
