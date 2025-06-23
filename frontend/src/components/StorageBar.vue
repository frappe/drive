<template>
  <div
    v-if="!totalStorage.loading"
    class="flex flex-col hover:bg-surface-gray-2 rounded cursor-pointer mb-0.5"
    @click="emitter.emit('showSettings', 2)"
  >
    <SidebarItem
      :label="props.isExpanded ? __('Storage') : '- used out of 5GB'"
      :is-collapsed="!props.isExpanded"
    >
      <template #icon>
        <LucideCloud class="w-4" />
      </template>
    </SidebarItem>
    <div class="w-auto mx-2 bg-surface-gray-4 rounded-full h-1 my-2">
      <div
        class="h-1 rounded-full"
        :class="
          (100 * usedStorage) / storageMax > 100
            ? 'bg-surface-red-500'
            : 'bg-surface-gray-7'
        "
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
      >{{ formattedString }}</span
    >
  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from "vue"
import { createResource } from "frappe-ui"
import SidebarItem from "./SidebarItem.vue"
import { formatSize, base2BlockSize } from "@/utils/format"
import { useRoute } from "vue-router"
import LucideCloud from "~icons/lucide/cloud"

const emitter = inject("emitter")

const usedStorage = ref(0)
const storageMax = ref(5368709120)

const props = defineProps(["isExpanded"])
const formattedString = computed(() => {
  return (
    (formatSize(usedStorage.value) || "-") +
    " used out of " +
    base2BlockSize(storageMax.value)
  )
})

const calculatePercent = computed(() => {
  let num = (100 * usedStorage.value) / storageMax.value
  return new Intl.NumberFormat("default", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(num / 100)
})
const route = useRoute()
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

let totalStorage = createResource({
  url: "drive.api.storage.storage_bar_data",
  method: "GET",
  cache: "total_storage",
  onSuccess(data) {
    usedStorage.value = data.total_size
    storageMax.value = data.limit
  },
})
watch(team, (val) => val && totalStorage.fetch({ team: val }), {
  immediate: true,
})

emitter.on("recalculate", () => {
  setTimeout(() => totalStorage.fetch({ team: team.value }), 2000)
})
</script>
