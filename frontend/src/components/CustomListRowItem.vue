<template>
  <ListRowItem
    :column="column"
    :row="row"
    :item="item"
    :align="column.align"
  >
    <template
      v-if="column.key === 'title'"
      #prefix
    >
      <img
        v-if="!imgLoaded"
        loading="lazy"
        class="h-[16px] w-[16px] rounded-sm"
        :src="backupLink"
        :draggable="false"
      >
      <img
        v-show="imgLoaded"
        class="h-[16px] w-[16px] object-cover rounded-sm"
        :src="src"
        :draggable="false"
        @error="src = backupLink"
        @load="imgLoaded = true"
      >
    </template>
    <template #default="{ label }">
      <div
        :key="label"
        class="truncate text-base"
      >
        {{ column?.getLabel ? column.getLabel({ row }) : label }}
      </div>

      <Button
        v-if="column.key === 'options' && contextMenu"
        class="!bg-inherit"
        @click="(e) => contextMenu(e, row)"
      >
        <LucideMoreHorizontal class="size-4" />
      </Button>
    </template>
    <template
      v-if="idx === 0"
      #suffix
    >
      <div class="flex flex-row grow justify-end gap-2 w-[20px]">
        <component
          :is="column.suffix({ row })"
          v-if="column.suffix"
        />
        <LucideStar
          v-if="row.is_favourite && $route.name !== 'Favourites'"
          name="star"
          width="16"
          height="16"
          class="my-auto stroke-amber-500 fill-amber-500"
        />
      </div>
    </template>
  </ListRowItem>
</template>
<script setup>
import { ListRowItem } from "frappe-ui"
import { ref } from "vue"

const props = defineProps({
  idx: Number,
  column: Object,
  row: Object,
  item: String,
  contextMenu: Function,
})

let src, imgLoaded, thumbnailLink, backupLink, _

if (props.column.prefix && props.column.key === "title") {
  ;[thumbnailLink, backupLink, _] = props.column.prefix({
    row: props.row,
  })

  src = ref(thumbnailLink || backupLink)
  imgLoaded = ref(false)
}
</script>
