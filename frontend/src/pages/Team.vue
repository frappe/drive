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
import { computed } from "vue"

const store = useStore()
const props = defineProps({
  team: String,
})
store.commit("setCurrentFolder", { name: "", team: props.team })

const write = computed(
  () =>
    allUsers.data &&
    allUsers.data.find((k) => k.name === store.state.user.id).access_level > 0
)
if (getTeams.data)
  store.commit("setBreadcrumbs", [
    {
      label: getTeams.data[useRoute().params.team]?.title,
      name: "Team",
    },
  ])
</script>
