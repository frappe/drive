<template>
  <GenericPage
    :get-entities="getShared"
    :icon="LucideUsers"
    primary-message="No shared files"
    secondary-message="You can share files easily on Drive - try it out!"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"

import { computed, watch } from "vue"
import { useStore } from "vuex"
import { getShared } from "@/resources/files"
import LucideUsers from "~icons/lucide/users"

const store = useStore()
const shareView = computed(() => store.state.shareView)
watch(
  shareView,
  (val) => {
    const oldParams = getShared.params
    getShared.params = { shared: val }
    getShared.fetch({ ...oldParams, ...getShared.params })
  },
  { immediate: true }
)
</script>
