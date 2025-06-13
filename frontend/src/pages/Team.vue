<template>
  <GenericPage
    :get-entities="getHome"
    :icon="LucideBuilding2"
    primary-message="Team is empty"
    secondary-message="Add files by dropping them here."
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getHome, getTeams } from "@/resources/files"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import { LucideBuilding2 } from "lucide-vue-next"

const store = useStore()
store.commit("setCurrentFolder", { name: "" })
if (getTeams.data)
  store.commit("setBreadcrumbs", [
    {
      label: getTeams.data[useRoute().params.team]?.title,
      name: "Team",
    },
  ])
</script>
