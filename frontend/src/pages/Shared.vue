<template>
  <GenericPage
    :getEntities="getShared"
    :icon="Users"
    :primaryMessage="'No Shared Files'"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Users from "@/components/EspressoIcons/Users.vue"

import { computed, watch } from "vue"
import { useStore } from "vuex"
import { getShared } from "@/resources/files"

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
