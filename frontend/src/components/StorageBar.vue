<template>
  <div
    v-if="!totalStorage.loading"
    class="flex flex-col hover:bg-gray-100 rounded cursor-pointer mb-0.5"
    @click="emitter.emit('showSettings', 2)"
  >
    <SidebarItem
      :label="props.isExpanded ? 'Storage' : '3.5GB used out of 50GB'"
      :is-collapsed="!props.isExpanded"
    >
      <template #icon>
        <Cloud class="w-4" />
      </template>
    </SidebarItem>
    <div class="w-auto mx-2 bg-gray-300 rounded-full h-1 my-2">
      <div
        class="h-1 rounded-full"
        :class="
          (100 * usedStorage) / storageMax > 100 ? 'bg-red-500' : 'bg-black'
        "
        :style="{
          width: calculatePercent,
          maxWidth: '100%',
        }"
      ></div>
    </div>
    <span
      class="mx-2 text-xs text-gray-600 transition-all duration-500 ease-in-out line-clamp-1"
      :class="
        isExpanded
          ? 'ml-2 w-auto opacity-100 h-auto'
          : 'ml-0 w-0 overflow-hidden opacity-0 h-0'
      "
      >{{ formatedString }}</span
    >
  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from "vue"
import { createResource } from "frappe-ui"
import { useRoute } from "vue-router"
import SidebarItem from "./SidebarItem.vue"
import Cloud from "./EspressoIcons/Cloud.vue"
import { formatSize, base2BlockSize } from "@/utils/format"
const emitter = inject("emitter")

const route = useRoute()

const usedStorage = ref(0)
const storageMax = ref(5368709120)

const props = defineProps(["isExpanded"])

const formatedString = computed(() => {
  return (
    formatSize(usedStorage.value) +
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
const team = localStorage.getItem("recentTeam")

let totalStorage = createResource({
  url: "drive.api.storage.storage_bar_data",
  params: {
    team,
  },
  method: "GET",
  cache: "total_storage",
  onSuccess(data) {
    usedStorage.value = data.total_size
    storageMax.value = data.limit
  },
})
totalStorage.fetch({ team })
</script>
