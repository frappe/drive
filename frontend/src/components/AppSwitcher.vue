<template>
  <Popover
    placement="right-start"
    class="flex w-full"
  >
    <template #target="{ togglePopover }">
      <Button
        @click="togglePopover"
        class="w-full !justify-start px-2"
        :class="[
          active ? 'bg-surface-gray-2' : 'text-ink-gray-8',
          'group w-full flex h-7 items-center justify-between rounded px-2 text-base hover:bg-surface-gray-2',
        ]"
        variant="ghost"
      >
        <template #icon>
          <AppsIcon class="size-4 text-ink-gray-6" />
          <span class="whitespace-nowrap text-base">Apps </span>
        </template>

        <template #suffix>
          <LucideChevronRight class="size-4 text-ink-gray-6 ml-auto" />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="flex w-full flex-col rounded-lg border border-outline-gray-2 bg-surface-white p-1.5 text-sm text-ink-gray-8 shadow-xl auto-fill-[100px] dark:bg-surface-gray-1"
      >
        <a
          :href="app.route"
          v-for="app in apps.data"
          key="name"
          class="flex items-center gap-2 rounded p-1 hover:bg-surface-gray-2"
        >
          <img
            class="size-6"
            :src="app.logo"
          />
          <span class="max-w-18 text-sm w-full truncate">
            {{ app.title }}
          </span>
        </a>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import AppsIcon from "@/components/AppsIcon.vue"
import { Popover, createResource, Button } from "frappe-ui"

const props = defineProps({
  active: Boolean,
})

const apps = createResource({
  url: "frappe.apps.get_apps",
  cache: "apps",
  auto: true,
  transform: (data) => {
    let apps = [
      {
        name: "frappe",
        logo: "/assets/frappe/images/framework.png",
        title: "Desk",
        route: "/app",
      },
    ]
    data.map((app) => {
      if (app.name === "drive") return
      apps.push({
        name: app.name,
        logo: app.logo,
        title: app.title,
        route: app.route,
      })
    })

    return apps
  },
})
</script>
