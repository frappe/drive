<template>
  <GenericPage
    :get-entities="getTeam"
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
import { getTeam, getTeams } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import LucideBuilding2 from "~icons/lucide/building-2"
import { computed } from "vue"

const store = useStore()
const props = defineProps({
  team: String,
})
store.commit("setCurrentFolder", { name: "", team: props.team })

const write = computed(
  () =>
    allUsers.data &&
    allUsers.data.find((k) => k.name === store.state.user.id)?.access_level > 0
)
const team = getTeams.data[useRoute().params.team]
store.commit("setBreadcrumbs", [
  {
    label: team.title,
    name: team.name,
  },
])
</script>
