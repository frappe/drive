<template>
  <TransitionGroup name="fade-in">
    <ListRow
      v-for="row in rows"
      :key="row.name"
      :row="row"
      class="rounded group"
      @click="$route.name !== 'Trash'"
      @contextmenu="(e) => contextMenu(e, row)"
      @mouseenter="$emit('mouseenter', row)"
      @mouseleave="$emit('mouseleave')"
      @dblclick="
        () => $route.name !== 'Trash' && openEntity(route.params.team, row)
      "
    >
      <template #default="{ idx, column, item }">
        <ListRowItem
          :column="column"
          :row="row"
          :item="item"
          :align="column.align"
        >
          <template #default="{ label }">
            <transition name="fade-in" mode="out-in">
              <div :key="label" class="truncate text-base">
                {{ column?.getLabel ? column.getLabel({ row }) : label }}
              </div>
            </transition>

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
                text="Your file alone."
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
import { openEntity } from "@/utils/files"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { LucideEyeOff } from "lucide-vue-next"
import Tooltip from "frappe-ui/src/components/Tooltip/Tooltip.vue"

defineProps({
  rows: Array,
  contextMenu: Function,
})
defineEmits(["mouseenter", "mouseleave"])
const route = useRoute()
const store = useStore()
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
