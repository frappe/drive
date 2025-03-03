<template>
  <ListRow
    v-for="row in rows"
    :class="selected(row) ? '!bg-surface-gray-2' : ''"
    :key="row.name"
    :row="row"
    class="hover:bg-surface-menu-bar cursor-pointer"
    @click="setActive(row)"
    @contextmenu="(e) => contextMenu(e, row)"
    @mouseenter="$emit('mouseenter', row)"
    @mouseleave="$emit('mouseleave')"
    @dblclick="() => openEntity(route.params.team, row)"
  >
    <template #default="{ idx, column, item }">
      <ListRowItem
        :column="column"
        :row="row"
        :item="item"
        :align="column.align"
      >
        <template v-if="idx === 0" #suffix>
          <div class="flex flex-row grow justify-end gap-2">
            <div v-if="hovered(row)">
              <FeatherIcon
                name="link"
                class="stroke-1.5 w-4 h-4"
                @click="getLink(row)"
              />
            </div>
            <FeatherIcon
              v-if="row.is_favourite && route.name !== 'Favourites'"
              name="star"
              width="16"
              height="16"
              class="stroke-amber-500 fill-amber-500"
            />
            <Lock
              v-else-if="
                row.is_private && store.state.breadcrumbs[0].label != 'Home'
              "
              width="16"
              height="16"
            />
            <FeatherIcon
              v-else-if="row.accessed && route.name !== 'Recents'"
              name="clock"
              width="16"
              height="16"
            />
          </div>
        </template>
        <template v-if="column.key === 'options'">
          <Button class="bg-white me-3" @click="(e) => contextMenu(e, row)">
            <FeatherIcon name="more-horizontal" class="h-4 w-4" />
          </Button>
        </template>
      </ListRowItem>
    </template>
  </ListRow>
</template>
<script setup>
import { FeatherIcon, ListRowItem, ListRow } from "frappe-ui"
import Lock from "./EspressoIcons/Lock.vue"
import { openEntity } from "@/utils/files"
import { getLink } from "@/utils/getLink"
import { ref } from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"

defineProps({
  rows: Array,
  contextMenu: Function,
  setActive: Function,
  selected: Function,
  hovered: Function,
})
defineEmits(["mouseenter", "mouseleave"])
const hoveredRow = ref(null)
const route = useRoute()
const store = useStore()
</script>
