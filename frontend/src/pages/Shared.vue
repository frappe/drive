<template>
  <GenericPage
    :getEntities="getShared"
    :icon="LucideUsers"
    :primaryMessage="'No Shared Files'"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"

import { computed, watch } from "vue"
import { useStore } from "vuex"
import { getShared } from "@/resources/files"

import { LucideUsers } from "lucide-vue-next"

const store = useStore()
const shareView = computed(() => store.state.shareView)

watch(
  shareView,
  (val) => {
    getShared.fetch({ by: val === "with" ? 0 : 1 })
  },
  { immediate: true }
)
</script>
