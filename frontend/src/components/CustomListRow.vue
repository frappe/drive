<template>
  <TransitionGroup name="fade-in">
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
      @click="settings.data.single_click && open(row)"
      @dblclick="!settings.data.single_click && open(row)"
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
              class="me-3 bg-inherit"
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
  </TransitionGroup>
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

// Used as right-click doesn't trigger active in frappe-ui
const selectedName = computed(() => store.state.activeEntity?.name)
const open = (row) =>
  route.name !== "Trash" && openEntity(route.params.team, row)
</script>

<style scoped>
.fade-in-enter-active {
  transition: opacity 300ms cubic-bezier(0.55, 0.085, 0.68, 0.53);
}

.fade-in-leave-active {
  transition: opacity 225ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.fade-in-enter,
.fade-in-leave-to {
  opacity: 0;
}
</style>
