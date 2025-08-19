<template>
  <GenericPage
    :get-entities="getShared"
    :icon="LucideUsers"
    :primary-message="__('No Shared Files')"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"

import { getShared } from "@/resources/files"
import { computed, watch } from "vue"
import { useStore } from "vuex"
import LucideUsers from "~icons/lucide/users"

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
