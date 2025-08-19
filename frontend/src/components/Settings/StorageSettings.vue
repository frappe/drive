<template>
  <h1 class="font-semibold mb-4 text-ink-gray-9">
    {{ __("Lưu trữ") }}
  </h1>

  <div class="flex items-center justify-between w-full mb-2">
    <span class="text-base font-medium text-ink-gray-8">
      {{ showFileStorage ? "Bạn đã" : "Nhóm của bạn đã" }} sử dụng
      {{ formatGB(usedSpace) }} trên tổng số {{ showFileStorage ? "của bạn" : "" }}
      {{ formatGB(spaceLimit) }} ({{
        formatPercent((usedSpace / spaceLimit) * 100)
      }})
    </span>

    <div
      class="bg-surface-gray-2 rounded-[10px] space-x-0.5 h-7 flex items-center px-0.5 py-1"
    >
      <TabButtons
        v-model="showFileStorage"
        :buttons="[
          {
            label: __('Của bạn'),
            value: true,
          },
          {
            label: __('Nhóm'),
            value: false,
          },
        ]"
      />
    </div>
  </div>

  <div
    v-if="usedSpace > 0"
    class="w-full flex justify-start items-start bg-surface-menu-bar border rounded overflow-clip h-7 pl-0 mb-4"
  >
    <Tooltip
      v-for="[file_kind, i] in storageBreakdown.data?.total"
      :key="file_kind"
    >
      <template #body>
        <div
          class="text-center rounded bg-surface-gray-7 px-2 py-1 text-xs text-ink-white shadow-xl"
        >
          {{ i.kind }} <br />{{ i.h_size }} ({{ i.percentageFormat }})
        </div>
      </template>
      <div
        class="h-7"
        :style="{
          backgroundColor: i.color,
          width: i.percentageFormat,
          paddingRight: `${1 + i.percentageRaw}px`,
        }"
      />
    </Tooltip>
  </div>

  <div
    v-else
    class="w-full flex flex-col items-center justify-center my-10"
  >
    <LucideCloud class="h-7 stroke-1 text-ink-gray-5" />
    <span class="text-ink-gray-8 text-sm mt-2">Chưa sử dụng dung lượng</span>
  </div>

  <div
    class="mt-1 text-ink-gray-8 font-medium text-base py-2"
    :class="storageBreakdown.data?.entities?.length ? 'border-b' : ''"
  >
    Tệp lớn:
  </div>

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
      <img :src="getIconUrl(i.file_type)" />
      <span class="text-ink-gray-8 text-sm truncate">{{ i.title }}</span>

      <div class="text-ink-gray-8 text-sm ml-auto flex gap-2 h-10 leading-10">
        <Button
          v-if="hoveredRow === i.name"
          variant="ghost"
          class="self-center"
          @click="openEntity($route.params.team, i), $emit('close')"
        >
          <LucideArrowRight class="size-4 text-ink-gray-5" />
        </Button>
        {{ formatSize(i.file_size) }}
      </div>
    </div>

    <div
      v-if="!storageBreakdown.data?.entities?.length"
      class="py-4 text-center w-full text-sm text-italic"
    >
      {{ __("Không tìm thấy tệp nào.") }}
    </div>
  </div>
</template>

<script setup>
import { MIME_LIST_MAP, openEntity } from "@/utils/files"
import { COLOR_MAP, formatPercent, formatSize } from "@/utils/format"
import { getIconUrl } from "@/utils/getIconUrl"
import { createResource, TabButtons, Tooltip } from "frappe-ui"
import { ref, watch } from "vue"
import { useRoute } from "vue-router"
import LucideArrowRight from "~icons/lucide/arrow-right"
import LucideCloud from "~icons/lucide/cloud"

const hoveredRow = ref(null)
const showFileStorage = ref(true)
const usedSpace = ref(0)
const spaceLimit = ref(0)
const route = useRoute()

function formatGB(bytes) {
  return (bytes / 1024 ** 3).toFixed(2) + " GB"
}

const storageBreakdown = createResource({
  url: "drive.api.storage.storage_breakdown",
  makeParams: (p) => p,
  onSuccess(data) {
    let res = {}
    usedSpace.value = 0

    spaceLimit.value = data.limit * 1024 * 1024

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
      res[kind].kind = kind
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
  (val) =>
    storageBreakdown.fetch({
      team: route.params.team || localStorage.getItem("recentTeam"),
      owned_only: val,
    }),
  { immediate: true }
)

defineEmits(["close"])
</script>
