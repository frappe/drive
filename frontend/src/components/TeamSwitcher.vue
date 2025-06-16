<template>
  <Popover
    placement="right-start"
    class="flex w-full"
  >
    <template #target="{ togglePopover }">
      <button
        :class="[
          active ? 'bg-surface-gray-2' : 'text-ink-gray-8',
          'group w-full flex h-7 items-center justify-between rounded px-2 text-base hover:bg-surface-gray-2',
        ]"
        @click.prevent="togglePopover()"
      >
        <div class="flex gap-2">
          <LucideUser class="size-4 text-ink-gray-6" />
          <span class="whitespace-nowrap"
            >{{ $route.params.team ? "Change Team" : "Go to" }}
          </span>
        </div>
        <LucideChevronRight class="size-4 text-ink-gray-6" />
      </button>
    </template>
    <template #body>
      <div
        class="mx-3 p-1 rounded-lg border border-gray-100 bg-surface-white shadow-xl"
      >
        <div
          v-for="team of teams"
          v-if="teams.length"
          :key="getTeams.data[team].name"
        >
          <router-link
            :to="{
              name: 'Home',
              params: { team: getTeams.data[team].name },
            }"
            class="block w-100 rounded justify-center items-center p-1 text-sm text-ink-gray-7 hover:bg-surface-gray-2"
            @click="LISTS.forEach((k) => k.reset())"
          >
            {{ getTeams.data[team].title }}
          </router-link>
        </div>
        <div
          v-else
          class="w-100 text-center text-sm text-ink-gray-7"
        >
          <em>No other teams</em>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import { Popover } from "frappe-ui"
import { getTeams } from "@/resources/files"
import { computed } from "vue"
import { useRoute } from "vue-router"
import { LISTS } from "@/resources/files"

getTeams.fetch()
const route = useRoute()
const teams = computed(() =>
  Object.keys(getTeams.data).filter((k) => k !== route.params.team)
)

defineProps({
  active: Boolean,
})
</script>
