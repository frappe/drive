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
  return store.state.shareView === "with"
    ? "drive.api.permissions.get_shared_with_me"
    : "drive.api.permissions.get_shared_by_me"
})
</script>
