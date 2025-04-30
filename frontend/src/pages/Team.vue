<template>
  <GenericPage
    :get-entities="getHome"
    :icon="Team"
    primary-message="Team is empty"
    secondary-message="Add files by dropping them here."
  />
</template>

<script setup>
import Team from "../components/EspressoIcons/Organization.vue"
import GenericPage from "@/components/GenericPage.vue"
import { getHome, getTeams } from "@/resources/files"
import { useStore } from "vuex"
import { useRoute } from "vue-router"

const store = useStore()
if (getTeams.data)
  store.commit("setBreadcrumbs", [
    {
      label: getTeams.data[useRoute().params.team]?.title,
      name: "Team",
    },
  ])
</script>
