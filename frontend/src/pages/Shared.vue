<template>
  <PageGeneric
    :key="sharedUrl"
    :url="sharedUrl"
    :allow-empty-context-menu="allowEmptyContextMenu"
    :show-sort="true"
    :icon="Users"
    :primaryMessage="'No Shared Files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue"
import { ref, computed } from "vue"
import { useStore } from "vuex"
import Users from "../components/EspressoIcons/Users.vue"

const store = useStore()
const allowEmptyContextMenu = ref(false)

const sharedUrl = computed(() => {
  if (store.state.user.role === "Drive Guest") {
    return store.state.shareView === "with"
      ? "drive.api.list.shared_with_guest"
      : "drive.api.list.shared_by_guest"
  }
  return store.state.shareView === "with"
    ? "drive.api.list.shared_with_user"
    : "drive.api.list.shared_by_user"
})
</script>
