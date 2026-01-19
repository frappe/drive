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

import { computed } from "vue"
import { useStore } from "vuex"
import { getSharedWith, getSharedBy } from "@/resources/files"
import LucideUsers from "~icons/lucide/users"

const store = useStore()
const shareView = computed(() => store.state.shareView)
const getShared = computed(() =>
  shareView.value === "with" ? getSharedWith : getSharedBy
)
</script>
