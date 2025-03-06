<template>
  <h1 class="font-semibold mb-4">Storage</h1>

  <div class="flex items-center justify-between w-full mb-2">
    <span class="text-base font-medium text-gray-900"
      >{{ showFileStorage ? "You have" : "The team has" }} used
      {{ formatSize(usedSpace) }} out of {{ showFileStorage ? "your" : "" }}
      {{ base2BlockSize(spaceLimit) }} ({{
        formatPercent((usedSpace / spaceLimit) * 100)
      }})</span
    >
    <div
      class="bg-gray-100 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
    >
      <Button
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          showFileStorage === true
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="showFileStorage = true"
      >
        You
      </Button>
      <Button
        variant="ghost"
        class="max-h-6 leading-none transition-colors focus:outline-none"
        :class="[
          showFileStorage === false
            ? 'bg-white shadow-sm hover:bg-white active:bg-white'
            : '',
        ]"
        @click="showFileStorage = false"
      >
        Team
      </Button>
    </div>
  </div>
  <div
    v-if="usedSpace > 0"
    class="w-full flex justify-start items-start bg-gray-50 border rounded overflow-clip h-7 pl-0 mb-4"
  >
    <Tooltip
      v-for="[file_kind, i] in storageBreakdown.data?.total"
      :key="file_kind"
      :text="`${i.h_size} (${i.percentageFormat})`"
    >
      <div
        class="h-7"
        :style="{
          backgroundColor: i.color,
          width: i.percentageFormat,
          paddingRight: `${1 + i.percentageRaw}px`,
        }"
      ></div>
    </Tooltip>
  </div>
  <div class="flex flex-wrap items-start justify-around gap-2 px-3 w-full">
    <div
      v-for="[file_kind, i] in storageBreakdown.data?.total"
      :bind="file_kind"
      class="flex py-1"
    >
      <div
        class="w-4 h-4 rounded-sm"
        :style="{ backgroundColor: i.color }"
      ></div>
      <span class="text-gray-800 text-sm ps-1">{{ file_kind }}</span>
    </div>
  </div>
  <div
    v-if="!usedSpace"
    class="h-full w-full flex flex-col items-center justify-center my-auto"
  >
    <Cloud class="h-7 stroke-1 text-gray-600" />
    <span class="text-gray-800 text-sm mt-2">No Storage Used</span>
  </div>
  <div class="mt-5 text-gray-800 text-base py-2 border-b">Large Files:</div>
  <div
    class="flex flex-col items-start justify-start w-full rounded full px-1.5 overflow-y-auto"
  >
    <div
      v-for="(i, index) in storageBreakdown.data?.entities"
      :key="i.name"
      class="w-full h-10 flex items-center justify-start py-3 gap-x-2"
      :class="index > 0 ? 'border-t' : ''"
      @mouseenter="hoveredRow = i.name"
      @mouseleave="hoveredRow = null"
    >
      <img :src="getIconUrl(formatMimeType(i.mime_type))" />
      <span class="text-gray-800 text-sm">{{ i.title }}</span>

      <div class="text-gray-800 text-sm ml-auto flex gap-2 h-10 leading-10">
        <div v-if="hoveredRow === i.name">
          <Button
            class="!p-1 !py-0 !h-6"
            variant="ghost"
            @click="openEntity($route.params.team, i), $emit('close')"
            ><FeatherIcon name="arrow-right" class="w-4 h-4 !p-0 text-gray-600"
          /></Button>
        </div>
        {{ formatSize(i.file_size) }}
      </div>
    </div>
  </div>
</template>
<script setup>
import {
  formatSize,
  base2BlockSize,
  formatMimeType,
  COLOR_MAP,
  formatPercent,
} from "@/utils/format"
import Cloud from "@/components/EspressoIcons/Cloud.vue"
import FeatherIcon from "frappe-ui/src/components/FeatherIcon.vue"
import { Tooltip } from "frappe-ui"
import { getIconUrl } from "@/utils/getIconUrl"
import { openEntity, MIME_LIST_MAP } from "@/utils/files"
import { createResource } from "frappe-ui"
import { ref, watch } from "vue"
import { useRoute } from "vue-router"

const hoveredRow = ref(null)
const showFileStorage = ref(true)
const usedSpace = ref(0)
const spaceLimit = ref(0)
const route = useRoute()

const storageBreakdown = createResource({
  url: "drive.api.storage.storage_breakdown",
  makeParams: (p) => p,
  onSuccess(data) {
    let res = {}
    usedSpace.value = 0
    spaceLimit.value = data.limit
    data.total.forEach((item) => {
      let kind =
        Object.entries(MIME_LIST_MAP).find(([type, list]) =>
          list.includes(item.mime_type) ? type : false
        )?.[0] || "Unknown"
      res[kind] = res[kind] || { file_size: 0 }
      res[kind].file_size += item.file_size
      usedSpace.value += item.file_size
    })
    Object.keys(res).forEach((kind) => {
      res[kind].color = COLOR_MAP[kind]
      res[kind].percentageRaw = (100 * res[kind].file_size) / spaceLimit.value
      res[kind].percentageFormat = formatPercent(res[kind].percentageRaw)
      res[kind].h_size = formatSize(res[kind].file_size)
    })
    data.total = Object.entries(res).sort(
      (a, b) => b[1].file_size - a[1].file_size
    )
  },
  auto: false,
})

watch(
  showFileStorage,
  (val) => storageBreakdown.fetch({ team: route.params.team, owned_only: val }),
  { immediate: true }
)

defineEmits(["close"])
</script>
