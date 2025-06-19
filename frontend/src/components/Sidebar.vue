<template>
  <div
    :class="isExpanded ? 'w-[220px]' : 'w-[50px]'"
    class="border-r bg-surface-menu-bar relative hidden sm:flex h-screen flex-col justify-start duration-300 ease-in-out p-2"
  >
    <PrimaryDropDown :is-expanded="isExpanded" />
    <div
      class="mt-2.5"
      :class="!isExpanded ? 'flex flex-col items-start' : ''"
      ondragstart="return false;"
      ondrop="return false;"
    >
      <SidebarItem
        :label="__('Go')"
        class="mb-1"
        :is-collapsed="!isExpanded"
        @click="() => emitter.emit('showSearchPopup', true)"
      >
        <template #icon>
          <LucideCommand class="size-4" />
        </template>
      </SidebarItem>
      <SidebarItem
        :icon="sidebarItems[0].icon"
        :label="sidebarItems[0].label"
        :to="sidebarItems[0].route"
        :is-collapsed="!isExpanded"
        class="mb-0.5"
      />
      <SidebarItem
        :label="'Inbox'"
        :icon="LucideInbox"
        class="mb-0.5"
        :is-collapsed="!isExpanded"
        :to="'/t/' + team + '/notifications'"
      >
        <template #right>
          <div
            v-if="isExpanded && notifCount.data > 0"
            class="flex items-center justify-start w-full duration-300 ease-in-out ml-2"
          >
            <span class="text-xs text-ink-gray-4 ease-in ml-auto">
              {{ notifCount.data }}
            </span>
          </div>
        </template>
      </SidebarItem>
      <SidebarItem
        v-for="item in sidebarItems.slice(1)"
        :key="item.label"
        :icon="item.icon"
        :label="item.label"
        :to="item.route"
        :is-collapsed="!isExpanded"
        class="mb-0.5"
      />
    </div>
    <div class="mt-auto">
      <StorageBar :is-expanded="isExpanded" />
      <SidebarItem
        :label="!isExpanded ? 'Expand' : 'Collapse'"
        :is-collapsed="!isExpanded"
        class="mt-auto py-4"
        @click="toggleExpanded"
      >
        <template #icon>
          <span class="grid h-4.5 w-4.5 flex-shrink-0 place-items-center">
            <ArrowLeftFromLine
              class="stroke-[1.5] size-4 text-ink-gray-7 duration-300 ease-in-out"
              :class="{ '[transform:rotateY(180deg)]': !isExpanded }"
            />
          </span>
        </template>
      </SidebarItem>
    </div>
  </div>
</template>
<script setup>
import PrimaryDropDown from "./PrimaryDropdown.vue"
import SidebarItem from "@/components/SidebarItem.vue"
import StorageBar from "./StorageBar.vue"

import { notifCount } from "@/resources/permissions"
import { getTeams } from "@/resources/files"

import { computed } from "vue"
import { useStore } from "vuex"
import { useRoute } from "vue-router"
import LucideClock from "~icons/lucide/clock"
import ArrowLeftFromLine from "~icons/lucide/arrow-left-from-line"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideUsers from "~icons/lucide/users"
import LucideTrash from "~icons/lucide/trash"
import LucideHome from "~icons/lucide/home"
import LucideStar from "~icons/lucide/star"
import LucideCommand from "~icons/lucide/command"
import LucideInbox from "~icons/lucide/inbox"

defineEmits(["toggleMobileSidebar", "showSearchPopUp"])
const store = useStore()
const route = useRoute()
notifCount.fetch()

const isExpanded = computed(() => store.state.IsSidebarExpanded)
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

const sidebarItems = computed(() => {
  const items = [
    {
      label: __("Home"),
      route: `/t/${team.value}/`,
      icon: LucideHome,
    },
    {
      label: __("Recents"),
      route: `/t/${team.value}/recents`,
      icon: LucideClock,
    },
    {
      label: __("Favourites"),
      route: `/t/${team.value}/favourites`,
      icon: LucideStar,
    },
    {
      label: __("Team"),
      route: `/t/${team.value}/team`,
      icon: LucideBuilding2,
    },
    {
      label: __("Shared"),
      route: `/shared/`,
      icon: LucideUsers,
    },
    {
      label: __("Trash"),
      route: `/t/${team.value}/trash`,
      icon: LucideTrash,
    },
  ]
  if (getTeams.data && getTeams.data[team.value]?.title === "Your Drive")
    items.splice(1, 1)
  return items
})

const toggleExpanded = () =>
  store.commit("setIsSidebarExpanded", isExpanded.value ? false : true)
</script>
