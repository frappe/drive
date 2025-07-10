<template>
  <div
    v-if="!totalStorage.loading"
    class="flex flex-col hover:bg-surface-gray-2 rounded cursor-pointer mb-0.5"
    @click="emitter.emit('showSettings', 2)"
  >
    <SidebarItem
      :label="props.isExpanded ? __('Storage') : `- used out of ${limitText}`"
      :is-collapsed="!props.isExpanded"
    >
      <template #icon>
        <LucideCloud class="w-4" />
      </template>
    </SidebarItem>
    <div class="w-auto mx-2 bg-surface-gray-4 rounded-full h-1 my-2">
      <div
        class="h-1 rounded-full"
        :class="usedPercent > 100 ? 'bg-surface-red-500' : 'bg-surface-gray-7'"
        :style="{
          width: calculatePercent,
          maxWidth: '100%',
        }"
      />
    </div>
    <span
      class="mx-2 text-xs text-ink-gray-5 transition-all duration-500 ease-in-out line-clamp-1"
      :class="
        isExpanded
          ? 'ml-2 w-auto opacity-100 h-auto'
          : 'ml-0 w-0 overflow-hidden opacity-0 h-0'
      "
    >
      {{ formattedString }}
    </span>
  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from "vue"
import { createResource } from "frappe-ui"
import SidebarItem from "./SidebarItem.vue"
import { useRoute } from "vue-router"
import LucideCloud from "~icons/lucide/cloud"

const emitter = inject("emitter")

const usedStorage = ref(0) // bytes
const storageMax = ref(0) // GB
const props = defineProps(["isExpanded"])

const route = useRoute()
const team = computed(() => {
  return route.params.team || localStorage.getItem("recentTeam") || ""
})

// Format hiển thị giới hạn dung lượng
const limitText = computed(() => {
  return `${storageMax.value.toFixed(1)} GB`
})

// Format chuỗi hiển thị chính
const formattedString = computed(() => {
  const usedGB = (usedStorage.value / 1024 ** 3).toFixed(2)
  return `${usedGB} GB used out of ${storageMax.value.toFixed(1)} GB`
})

// Tính phần trăm đã sử dụng
const usedPercent = computed(() => {
  return ((usedStorage.value / (storageMax.value * 1024 ** 3)) * 100).toFixed(1)
})

const calculatePercent = computed(() => {
  return `${usedPercent.value}%`
})

// Resource gọi API
let totalStorage = createResource({
  url: "drive.api.storage.storage_bar_data",
  method: "GET",
  cache: "total_storage",
  onSuccess(data) {
    usedStorage.value = data.total_size || 0 // bytes
    storageMax.value = data.limit || 0 // đơn vị GB (KHÔNG chia lại!)
  },
})

// Gọi API khi thay đổi team
watch(
  team,
  (val) => {
    if (val) totalStorage.fetch({ team: val })
  },
  { immediate: true }
)

// Lắng nghe sự kiện làm mới
emitter.on("recalculate", () => {
  setTimeout(() => {
    if (team.value) totalStorage.fetch({ team: team.value })
  }, 2000)
})
</script>
