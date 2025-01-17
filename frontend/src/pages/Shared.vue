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

const sharedURL = computed(() => {
  let suffix
  if (store.state.user.role === "Drive Guest")
    suffix = store.state.shareView === "with" ? "with_guest" : "by_guest"
  else suffix = store.state.shareView === "with" ? "with_user" : "by_user"
  return `drive.api.list.shared_${suffix}`
})

watch(sharedURL, () => {
  getShared.update({
    url: sharedURL,
  })
  getShared.fetch()
})
</script>
