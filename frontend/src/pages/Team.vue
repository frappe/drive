<template>
  <GenericPage
    :get-entities="getHome"
    :icon="LucideBuilding2"
    primary-message="Team is empty"
    secondary-message="Add files by dropping them here."
    :verify="{
      data: {
        write,
      },
    }"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getHome, getTeams } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import LucideBuilding2 from "~icons/lucide/building-2"
import { computed, watch } from "vue"

const store = useStore()
const route = useRoute()
store.commit("setCurrentFolder", { name: "" })

const write = computed(
  () =>
    allUsers.data &&
    allUsers.data.find((k) => k.name === store.state.user.id).access_level > 0
)

// Set breadcrumbs when teams data is available
const setBreadcrumbs = () => {
  if (getTeams.data && route.params.team) {
    const currentTeam = getTeams.data[route.params.team]
    if (currentTeam) {
      store.commit("setBreadcrumbs", [
        {
          label: currentTeam.title,
          name: "Team",
        },
      ])
    }
  }
}

// Set breadcrumbs immediately if data is available
setBreadcrumbs()

// Watch for teams data changes
watch(() => getTeams.data, setBreadcrumbs, { immediate: true })
</script>
