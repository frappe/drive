<template>
  <ListRow
    v-for="row in rows"
    :key="row.name"
    :row="row"
    class="rounded"
    @click="$route.name !== 'Trash'"
    @contextmenu="(e) => contextMenu(e, row)"
    @mouseenter="$emit('mouseenter', row)"
    @mouseleave="$emit('mouseleave')"
    @dblclick="
      () => $route.name !== 'Trash' && openEntity(route.params.team, row)
    "
  >
    <template #default="{ idx, column, item, isHovered }">
      <ListRowItem
        :column="column"
        :row="row"
        :item="item"
        :align="column.align"
      >
        <template #default="{ label }">
          <div class="truncate text-base max-w-[70%]">
            {{ column?.getLabel ? column.getLabel({ row }) : label }}
          </div>

          <Button
            v-if="column.key === 'options'"
            class="bg-white me-3"
            @click="(e) => contextMenu(e, row)"
          >
            <FeatherIcon name="more-horizontal" class="h-4 w-4" />
          </Button>
        </template>
        <template v-if="idx === 0" #suffix>
          <div class="flex flex-row grow justify-end gap-2 w-[50px]">
            <Button v-if="isHovered" variant="ghost">
              <FeatherIcon
                name="link"
                class="stroke-1.5 w-4 h-4"
                @click.once="getLink(row)"
                @dblclick.stop
              />
            </Button>
            <Button
              v-if="row.is_favourite && route.name !== 'Favourites'"
              variant="ghost"
            >
              <FeatherIcon
                name="star"
                width="16"
                height="16"
                class="my-auto stroke-amber-500 fill-amber-500"
              />
            </Button>
            <Button
              v-else-if="row.accessed && route.name !== 'Recents'"
              variant="ghost"
            >
              <FeatherIcon
                name="clock"
                class="my-auto"
                width="16"
                height="16"
              />
            </Button>
            <Lock
              v-else-if="
                row.is_private && store.state.breadcrumbs[0].label != 'Home'
              "
              width="16"
              height="16"
              class="my-auto"
            />
          </div>
        </template>
      </ListRowItem>
    </template>
  </ListRow>
</template>
<script setup>
import { FeatherIcon, ListRowItem, ListRow, Tooltip } from "frappe-ui"
import Lock from "./EspressoIcons/Lock.vue"
import { openEntity } from "@/utils/files"
import { getLink } from "@/utils/getLink"
import { useRoute } from "vue-router"
import { useStore } from "vuex"

defineProps({
  rows: Array,
  contextMenu: Function,
})
defineEmits(["mouseenter", "mouseleave"])
const route = useRoute()
const store = useStore()
</script>
