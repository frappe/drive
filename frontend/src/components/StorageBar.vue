<template>
  <div
    v-if="!storageBar.loading"
    class="flex flex-col hover:bg-surface-gray-2 rounded cursor-pointer mb-0.5"
    @click="emitter.emit('showSettings', 2)"
  >
    <SidebarItem
      :label="__('Storage')"
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
          (100 * storageBar.data.total_size) / storageMax > 100
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
      class="text-xs text-ink-gray-5 line-clamp-1 ml-2"
      :class="isExpanded ? 'opacity-100' : 'opacity-0'"
      >{{ formattedString }}</span
    >
  </div>
</template>

<script setup>
import { computed, inject, watch } from "vue"
import { createResource } from "frappe-ui"
import SidebarItem from "./SidebarItem.vue"
import { formatSize, base2BlockSize } from "@/utils/format"
import { storageBar } from "@/resources/files"
import { useRoute } from "vue-router"
import LucideCloud from "~icons/lucide/cloud"

const emitter = inject("emitter")

const storageMax = computed(() => storageBar.data.limit || 5368709120)

const props = defineProps(["isExpanded"])
const formattedString = computed(() => {
  return (
    formatSize(storageBar.data.total_size || 0) +
    " used out of " +
    base2BlockSize(storageMax.value)
  )
})

const calculatePercent = computed(() => {
  let num = (100 * storageBar.data.total_size) / storageMax.value
  return new Intl.NumberFormat("default", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(num / 100)
})
const route = useRoute()
const team = computed(() => route.params.team)

watch(team, (val) => storageBar.fetch({ team: val || "" }), {
  immediate: true,
})
</script>
