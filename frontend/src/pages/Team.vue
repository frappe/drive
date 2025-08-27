<template>
  <div class="flex flex-row">
    <div class="w-full">
      <GenericPage
        :get-entities="getHome"
        :icon="LucideBuilding2"
        primary-message="Không có tài liệu trong nhóm"
        secondary-message="Thả tệp vào đây để thêm."
        :verify="{
          data: {
            write,
          },
        }"
        @show-team-members="showTeamMembersList = true"
      />
    </div>
    <TeamMembersList v-if="showTeamMembersList" class="!h-[100vh]" @close="showTeamMembersList = false" />
  </div>
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getHome, getTeams } from "@/resources/files"
import { allUsers } from "@/resources/permissions"
import { computed, watch, ref } from "vue"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import LucideBuilding2 from "~icons/lucide/building-2"

const store = useStore()
const route = useRoute()

const showTeamMembersList = ref(true)

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

setBreadcrumbs()
watch(() => getTeams.data, setBreadcrumbs, { immediate: true })
</script>
