<template>
  <div class="flex flex-col hover:bg-gray-100 rounded cursor-pointer mb-0.5">
    <SidebarItem
      :label="isExpanded ? 'Storage' : '3.5GB used out of 50GB'"
      :is-collapsed="!isExpanded"
      @click="emitter.emit('showSettings', 2)"
    >
      <template #icon>
        <Cloud class="w-4" />
      </template>
    </SidebarItem>
    <div class="w-auto mx-2 bg-gray-300 rounded-full h-1 my-2">
      <div
        class="bg-black h-1 rounded-full"
        :style="{
          width: calculatePercent,
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
import { ref, computed, inject } from "vue"
import { useStore } from "vuex"
import { createResource } from "frappe-ui"
import SidebarItem from "./SidebarItem.vue"
import Cloud from "./EspressoIcons/Cloud.vue"
import { formatSize } from "@/utils/format"
const emitter = inject("emitter")
const usedStorage = ref(0)
const store = useStore()
const isExpanded = computed(() => {
  return store.state.IsSidebarExpanded
})

const formatedString = computed(() => {
  return (
    formatSize(usedStorage.value) +
    " used out of " +
    formatSize(maxStorage.data?.storage_limit)
  )
})

const calculatePercent = computed(() => {
  let num = (100 * storageUsed.data) / maxStorage.data?.storage_limit
  return new Intl.NumberFormat("default", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(num / 100)
})

let maxStorage = createResource({
  url: "frappe.client.get",
  method: "GET",
  cache: "max_storage",
  params: {
    doctype: "Drive Instance Settings",
  },
  onError(error) {
    if (error.messages) {
      console.log(error.messages)
    }
  },
  auto: true,
})

let storageUsed = createResource({
  url: "drive.api.files.total_storage_used",
  onSuccess(data) {
    data = data[0].total_size
    if (!data) data = 0
    usedStorage.value = data
  },
  onError(error) {
    if (error.messages) {
      console.log(error.messages)
    }
  },
  auto: true,
})
</script>
