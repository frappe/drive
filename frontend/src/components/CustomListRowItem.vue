<template>
  <ListRowItem :column="column" :row="row" :item="item" :align="column.align">
    <template v-if="column.key === 'title'" #prefix>
      <template v-if="is_image || !getThumbnail?.data">
        <img
          v-if="!imgLoaded"
          loading="lazy"
          class="h-[16px]"
          :src="backupLink"
          :draggable="false"
        />
        <img
          v-show="imgLoaded"
          class="h-[16px]"
          :src="src"
          @error="src = backupLink"
          @load="imgLoaded = true"
          :draggable="false"
        />
      </template>
      <!-- Direct padding doesn't work -->
      <div
        v-else
        class="overflow-hidden text-ellipsis whitespace-nowrap w-[16px] h-[16px]"
      >
        <div
          v-html="getThumbnail.data"
          class="prose prose-sm pointer-events-none ml-0 origin-top-left scale-[.05]"
        ></div>
      </div>
    </template>
    <template #default="{ label }">
      <transition v-if="column.key === 'title'" name="fade-in" mode="out-in">
        <div :key="label" class="truncate text-base">
          {{ column?.getLabel ? column.getLabel({ row }) : label }}
        </div>
      </transition>
      <div v-else :key="label" class="truncate text-base">
        {{ column?.getLabel ? column.getLabel({ row }) : label }}
      </div>

      <Button
        v-if="column.key === 'options'"
        class="!bg-inherit"
        @click="(e) => contextMenu(e, row)"
      >
        <FeatherIcon name="more-horizontal" class="h-4 w-4" />
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
            row.is_private &&
            !['Home', 'Shared'].includes($store.state.breadcrumbs[0].name)
          "
          text="This is from your Home."
        >
          <LucideEyeOff width="16" height="16" class="my-auto" />
        </Tooltip>
      </div>
    </template>
  </ListRowItem>
</template>
<script setup>
import { FeatherIcon, ListRowItem, Tooltip, createResource } from "frappe-ui"
import { ref } from "vue"
const props = defineProps({
  idx: Number,
  column: Object,
  row: Object,
  item: String,
})

let src, imgLoaded, thumbnailLink, backupLink, is_image, getThumbnail

if (props.column.prefix && props.column.key === "title") {
  ;[thumbnailLink, backupLink, is_image] = props.column.prefix({
    row: props.row,
  })

  src = ref(thumbnailLink || backupLink)
  imgLoaded = ref(false)
  if (!is_image) {
    getThumbnail = createResource({
      url: thumbnailLink,
      auto: true,
    })
  }
}
</script>
