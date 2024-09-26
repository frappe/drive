<template>
  <div>
    <div class="flex items-center w-full mb-2 justify-between">
      <span class="text-base font-medium text-gray-900"
        >Used {{ formatSize(usedSpace) }} out of
        {{ base2BlockSize(planSizeLimit) }}</span
      >
      <slot name="control"></slot>
    </div>
    <div
      v-if="usedSpace > 0"
      class="w-full flex justify-start items-start bg-gray-50 border rounded overflow-clip h-7 pl-0 mb-4"
    >
      <div
        v-for="i in entities"
        :key="i.file_kind"
        class="h-7"
        :style="{
          backgroundColor: i.color,
          width: i.percentageFormat,
          paddingRight: `${5 + i.percentageRaw}px`,
        }"
      ></div>
    </div>
  </div>
  <div
    v-if="!usedSpace"
    class="h-full w-full flex flex-col items-center justify-center my-auto"
  >
    <Cloud class="h-7 stroke-1 text-gray-600" />
    <span class="text-gray-800 text-sm mt-2">No Storage Used</span>
  </div>
  <div
    class="flex flex-col items-start justify-start w-full rounded full px-1.5 overflow-y-auto"
  >
    <div
      v-for="(i, index) in entities"
      :key="i.file_kind"
      class="w-full flex items-center justify-start py-3 gap-x-2"
      :class="index > 0 ? 'border-t' : ''"
    >
      <div
        class="h-2 w-2 rounded-full"
        :style="{
          backgroundColor: i.color,
        }"
      ></div>
      <span class="text-gray-800 text-sm">{{ i.file_kind }}</span>
      <span class="text-gray-800 text-sm ml-auto">{{ i.h_size }}</span>
    </div>
  </div>
</template>
<script setup>
import Cloud from "@/components/EspressoIcons/Cloud.vue"
import { formatSize, base2BlockSize } from "../../utils/format"

const props = defineProps({
  planSizeLimit: {
    type: Number,
  },
  usedSpace: {
    type: Number,
  },
  entities: {
    type: Object,
  },
  total: {
    type: Object,
  },
})
</script>
