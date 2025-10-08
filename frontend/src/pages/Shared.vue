<template>
  <GenericPage
    :get-entities="getShared"
    :empty="{
      icon: LucideUsers,
      title: 'No shared files',
      description: 'You can share files easily on Drive - try it out!',
    }"
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
