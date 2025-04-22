<template>
  <TransitionGroup>
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
            <transition name="slide-fade" mode="out-in">
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
import Lock from "./EspressoIcons/Lock.vue"
import { openEntity } from "@/utils/files"
import { getLink } from "@/utils/getLink"
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
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
  filter: blur(0);
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(2px);
  filter: blur(10px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  filter: blur(10px);
}
</style>
