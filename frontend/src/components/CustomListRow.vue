<template>
  <template v-for="row in rows" :key="row.name">
    <ListRow
      :row="row"
      class="group"
      :class="[
        row.name === selectedName
          ? 'bg-surface-gray-3 hover:!bg-surface-gray-3'
          : '',
        draggedItem === row.name ? 'opacity-60 hover:shadow-none' : '',
      ]"
      @contextmenu="(e) => contextMenu(e, row)"
      @[action]="open(row)"
      :draggable="true"
      @dragstart="draggedItem = row.name"
      @dragend="draggedItem = null"
      @dragover="row.is_group && $event.preventDefault()"
      @drop="$emit('dropped', row, draggedItem)"
    >
      <template #default="{ idx, column, item }">
        <CustomListRowItem :column :row :item :idx />
      </template>
    </ListRow>
  </template>
</template>
<script setup>
import { FeatherIcon, ListRowItem, ListRow, Tooltip } from "frappe-ui"
import CustomListRowItem from "./CustomListRowItem.vue"
import { openEntity } from "@/utils/files"
import { settings } from "@/resources/permissions"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { computed, ref } from "vue"

defineProps({
  rows: Array,
  contextMenu: Function,
})
const emit = defineEmits(["dropped"])

const draggedItem = ref()

const route = useRoute()
const store = useStore()
const action = computed(() =>
  (settings.data.message || settings.data).single_click ? "click" : "dblclick"
)

// Used as right-click doesn't trigger active in frappe-ui
const selectedName = computed(() => store.state.activeEntity?.name)
const open = (row) =>
  route.name !== "Trash" && openEntity(route.params.team, row)
</script>
