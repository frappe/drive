<template>
  <ListRowItem :column="column" :row="row" :item="item" :align="column.align">
    <template v-if="column.key === 'file_name'" #prefix>
      <img
        v-if="!imgLoaded"
        loading="lazy"
        class="h-[16px] w-[16px] rounded-sm"
        :src="fallback"
        :draggable="false"
      />
      <img
        v-show="imgLoaded"
        class="h-[16px] w-[16px] object-cover rounded-sm"
        :src="src"
        :draggable="false"
        @load="imgLoaded = true"
      />
    </template>
    <template #default="{ label }">
      <div :key="label" class="truncate text-base">
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
    <template v-if="idx === 0" #suffix>
      <div class="flex flex-row grow justify-end gap-2 w-[20px]">
        <LucideStar
          v-if="row.is_favourite && $route.name !== 'Favourites'"
          name="star"
          width="16"
          height="16"
          class="my-auto text-ink-amber-6 stroke-current fill-current"
        />
        <component :is="column.suffix({ row })" v-if="column.suffix" />
      </div>
    </template>
  </ListRowItem>
</template>
<script setup>
import { ListRowItem } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  idx: Number,
  column: Object,
  row: Object,
  item: String,
  contextMenu: Function,
})

const isFileColumn = props.column.prefix && props.column.key === 'file_name'
const { src, fallback } = isFileColumn ? props.column.prefix({ row: props.row }) : {}
const imgLoaded = ref(false)
</script>
