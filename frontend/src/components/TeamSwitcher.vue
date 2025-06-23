<template>
  <Popover
    placement="right-start"
    class="flex w-full"
  >
    <template #target="{ togglePopover }">
      <Button
        @click="togglePopover"
        class="w-full px-2 flex justify-between h-7 items-center"
        variant="ghost"
      >
        <template #icon>
          <LucideUser class="size-4 text-ink-gray-6" />
          <span class="whitespace-nowrap text-base"
            >{{ $route.params.team ? "Change Team" : "Go to" }}
          </span>
        </template>

        <template #suffix>
          <LucideChevronRight class="size-4 text-ink-gray-6 ml-auto" />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="p-1 rounded-lg border border-outline-gray-2 text-ink-gray-8 bg-surface-white shadow-xl"
      >
        <button
          v-if="teams.length"
          v-for="team of teams"
          class="group flex h-7 w-full items-center rounded px-2 text-sm p-1 hover:bg-surface-gray-2"
          :key="getTeams.data[team].name"
        >
          <router-link
            :to="{
              name: 'Home',
              params: { team: getTeams.data[team].name },
            }"
            @click="LISTS.forEach((k) => k.reset())"
          >
            {{ getTeams.data[team].title }}
          </router-link>
        </button>
        <div
          v-else
          class="w-full text-sm text-ink-gray-7 h-7 flex justify-center items-center"
        >
          <div>No other teams</div>
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
