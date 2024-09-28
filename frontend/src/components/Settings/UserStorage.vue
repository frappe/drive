<template>
  <div class="flex items-center justify-between w-full mb-2">
    <span class="text-base font-medium text-gray-900"
      >You have used {{ formatSize(usedSpace) }} out of
      {{ base2BlockSize(planSizeLimit) }}</span
    >
    <slot name="control"></slot>
  </div>
  <div
    v-if="usedSpace > 0"
    class="w-full flex justify-start items-start bg-gray-50 border rounded overflow-clip h-7 pl-0 mb-4"
  >
    <div
      v-for="i in data?.total"
      :key="i.file_kind"
      class="h-7"
      :style="{
        backgroundColor: i.color,
        width: i.percentageFormat,
        paddingRight: `${5 + i.percentageRaw}px`,
      }"
    ></div>
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
      v-for="(i, index) in data?.entities"
      :key="i.name"
      class="w-full flex items-center justify-start py-3 gap-x-2"
      :class="index > 0 ? 'border-t' : ''"
    >
      <img :src="getIconUrl(formatMimeType(i.mime_type))" />
      <span class="text-gray-800 text-sm">{{ i.title }}</span>
      <span class="text-gray-800 text-sm ml-auto">{{
        formatSize(i.file_size)
      }}</span>
    </div>
  </div>
</template>
<script setup>
import Cloud from "@/components/EspressoIcons/Cloud.vue"
import { formatSize, base2BlockSize, formatMimeType } from "../../utils/format"
import { getIconUrl } from "../../utils/getIconUrl"

const props = defineProps({
  data: {
    type: Object,
  },
  planSizeLimit: {
    type: Number,
  },
  usedSpace: {
    type: Number,
  },
})
</script>
