<template>
  <GenericPage
    :get-entities="getTeam"
    :icon="LucideBuilding2"
    :empty="{
      title: 'This team is empty',
      description: 'Add files by dropping them here.',
    }"
    :verify="{
      data: {
        write,
        upload: write,
      },
    }"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getTeam, getTeams, getPublicTeams } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import LucideBuilding2 from "~icons/lucide/building-2"
import { computed, watch } from "vue"

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
const route = useRoute()
const teamData = computed(
  () =>
    getTeams.data?.[route.params?.team] ||
    getPublicTeams.data?.[route.params?.team]
)
watch(() => getPublicTeams.data, console.log)
if (getPublicTeams.data) getPublicTeams.fetch()
watch(
  teamData,
  (t) =>
    t &&
    store.commit("setBreadcrumbs", [
      {
        label: t.title,
        name: t.name,
      },
    ]),
  { immediate: true }
)
</script>
