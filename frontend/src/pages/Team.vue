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
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import LucideBuilding2 from "~icons/lucide/building-2"
import { computed, watch } from "vue"

const store = useStore()
const props = defineProps({
  team: String,
})
store.commit("setCurrentFolder", { name: "", team: props.team })

const route = useRoute()
const teamData = computed(
  () =>
    getTeams.data?.[route.params?.team] ||
    getPublicTeams.data?.[route.params?.team]
)
const write = computed(
  () =>
    teamData.value?.users?.find((k) => k.user === store.state.user.id)
      ?.access_level > 0
)
watch(() => getPublicTeams.data, console.log)
if (!getPublicTeams.data) getPublicTeams.fetch()
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
