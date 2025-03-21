<template>
  <Popover placement="right-start" class="flex w-full">
    <template #target="{ togglePopover }">
      <button
        :class="[
          active ? 'bg-gray-100' : 'text-gray-800',
          'group w-full flex h-7 items-center justify-between rounded px-2 text-base hover:bg-gray-100',
        ]"
        @click.prevent="togglePopover()"
      >
        <div class="flex gap-2">
          <FeatherIcon name="user" class="size-4 text-gray-600" />
          <span class="whitespace-nowrap"
            >{{ $route.params.team ? "Change" : "Go to" }} Team</span
          >
        </div>
        <FeatherIcon name="chevron-right" class="size-4 text-gray-600" />
      </button>
    </template>
    <template #body>
      <div
        class="mx-3 p-1 rounded-lg border border-gray-100 bg-white shadow-xl"
      >
        <div
          v-if="teams.length"
          v-for="team of teams"
          :key="getTeams.data[team].name"
        >
          <router-link
            :to="{
              name: 'Home',
              params: { team: getTeams.data[team].name },
            }"
            class="block w-100 rounded justify-center items-center p-1 text-sm text-gray-700 hover:bg-gray-100"
          >
            {{ getTeams.data[team].title }}
          </router-link>
        </div>
        <div v-else class="w-100 text-center text-sm text-gray-700">
          <em>No other teams</em>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import { Popover } from "frappe-ui"
import { FeatherIcon } from "frappe-ui"
import { getTeams } from "@/resources/files"
import { computed, ref, watch } from "vue"

const storage = ref(window.localStorage)
watch(storage, console.log)

getTeams.fetch()
const teams = computed(() =>
  Object.keys(getTeams.data).filter(
    (t) => t !== localStorage.getItem("recentTeam")
  )
)

defineProps({
  active: Boolean,
})
</script>
