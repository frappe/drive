<template>
  <ListRow
    v-for="row in rows"
    :key="row.name"
    :row="row"
    class="group"
    :class="
      row.name === selectedName
        ? 'bg-surface-gray-3 hover:!bg-surface-gray-3'
        : ''
    "
    @contextmenu="(e) => contextMenu(e, row)"
    @[action]="open(row)"
  >
    <template #default="{ idx, column, item }">
      <ListRowItem
        :column="column"
        :row="row"
        :item="item"
        :align="column.align"
      >
        <template #default="{ label }">
          <transition
            v-if="column.key === 'title'"
            name="fade-in"
            mode="out-in"
          >
            <div :key="label" class="truncate text-base">
              {{ column?.getLabel ? column.getLabel({ row }) : label }}
            </div>
          </transition>
          <div v-else :key="label" class="truncate text-base">
            {{ column?.getLabel ? column.getLabel({ row }) : label }}
          </div>

          <Button
            v-if="column.key === 'options'"
            class="me-3 !bg-inherit"
            @click="(e) => contextMenu(e, row)"
          >
            <FeatherIcon
              name="more-horizontal"
              class="bg-transparent h-4 w-4"
            />
          </Button>
        </template>
        <template v-if="idx === 0" #suffix>
          <div class="flex flex-row grow justify-end gap-2 w-[20px]">
            <FeatherIcon
              v-if="row.is_favourite && route.name !== 'Favourites'"
              name="star"
              width="16"
              height="16"
              class="my-auto stroke-amber-500 fill-amber-500"
            />
            <Tooltip
              v-else-if="
                row.is_private && store.state.breadcrumbs[0].label != 'Home'
              "
              text="This is from your Home."
            >
              <LucideEyeOff width="16" height="16" class="my-auto" />
            </Tooltip>
          </div>
        </template>
      </ListRowItem>
    </template>
  </ListRow>
</template>
<script setup>
import { FeatherIcon, ListRowItem, ListRow } from "frappe-ui"
import Tooltip from "frappe-ui/src/components/Tooltip/Tooltip.vue"
import { openEntity } from "@/utils/files"
import { settings } from "@/resources/permissions"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { computed } from "vue"

defineProps({
  rows: Array,
  contextMenu: Function,
})
const route = useRoute()
const store = useStore()
console.log(settings.data)
const action = (settings.data.message || settings.data).single_click
  ? "click"
  : "dblclick"

// Used as right-click doesn't trigger active in frappe-ui
const selectedName = computed(() => store.state.activeEntity?.name)
const open = (row) =>
  route.name !== "Trash" && openEntity(route.params.team, row)
</script>
