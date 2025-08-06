<template>
  <Sidebar
    v-model:collapsed="isCollapsed"
    class="hidden sm:flex"
    :header="{
      title: getTeams.data?.[$route.params.team]?.title || 'Drive',
      subtitle: $store.state.user.fullName,
      menuItems: settingsItems,
      logo: FrappeDriveLogo,
    }"
    :sections="sidebarItems"
  >
    <template #footer-items="{ isCollapsed }">
      <StorageBar :is-expanded="!isCollapsed" />
    </template>
  </Sidebar>
  <SettingsDialog
    v-if="showSettings"
    v-model="showSettings"
    :suggested-tab="suggestedTab"
  />
  <ShortcutsDialog
    v-if="showShortcuts"
    v-model="showShortcuts"
  />
</template>
<script setup>
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"

import StorageBar from "./StorageBar.vue"
import { Sidebar, createResource } from "frappe-ui"

import { notifCount } from "@/resources/permissions"
import { getTeams } from "@/resources/files"

import { useStore } from "vuex"
import LucideClock from "~icons/lucide/clock"
import LucideBuilding2 from "~icons/lucide/building-2"
import LucideUsers from "~icons/lucide/users"
import LucideTrash from "~icons/lucide/trash"
import LucideHome from "~icons/lucide/home"
import LucideStar from "~icons/lucide/star"
import LucideInbox from "~icons/lucide/inbox"
import LucideSearch from "~icons/lucide/search"
import LucideFileText from "~icons/lucide/file-text"

import SettingsDialog from "@/components/Settings/SettingsDialog.vue"
import ShortcutsDialog from "@/components/ShortcutsDialog.vue"
import emitter from "@/emitter"
import { ref, computed, watch, shallowRef, onMounted, h } from "vue"
import AppsIcon from "@/components/AppsIcon.vue"
import { useRoute } from "vue-router"

import LucideBook from "~icons/lucide/book"
import LucideBadgeHelp from "~icons/lucide/badge-help"
import LucideMoon from "~icons/lucide/moon"

defineEmits(["toggleMobileSidebar", "showSearchPopUp"])
const store = useStore()
const route = useRoute()
notifCount.fetch()

const isCollapsed = ref(store.state.sidebarCollapsed)
const team = computed(
  () => route.params.team || localStorage.getItem("recentTeam")
)

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

const showSettings = ref(false)
const showShortcuts = ref(false)
const suggestedTab = ref(0)
emitter.on("showSettings", (val = 0) => {
  showSettings.value = true
  suggestedTab.value = val
})
emitter.on("toggleShortcuts", () => {
  showShortcuts.value = !showShortcuts.value
})
const settingsItems = shallowRef([
  {
    group: __("Manage"),
    hideLabel: true,
    items: [
      {
        icon: LucideUser,
        label: __(route.params.team ? "Switch Team" : "Go to"),
        submenu: [],
      },
      {
        icon: AppsIcon,
        label: __("Apps"),
        submenu: [],
      },
      {
        icon: LucideBook,
        label: __("Documentation"),
        onClick: () => window.open("https://docs.frappe.io/drive", "_blank"),
      },
      {
        icon: LucideBadgeHelp,
        label: __("Support"),
        onClick: () => window.open("https://t.me/frappedrive", "_blank"),
      },
      {
        icon: LucideMoon,
        label: "Toggle theme",
        onClick: toggleTheme,
      },
    ],
  },
  {
    group: __("Others"),
    hideLabel: true,
    items: [
      {
        icon: "settings",
        label: __("Settings"),
        onClick: () => (showSettings.value = true),
      },
      {
        icon: "log-out",
        label: __("Log out"),
        onClick: logout,
      },
    ],
  },
])

watch(
  [() => apps.data, () => getTeams.data],
  ([a, b]) => {
    if (!a || !b) return
    const teams = Object.entries(b).filter(([k, _]) => k !== route.params.team)
    let appsMenuIndex = 1
    if (!teams.length) {
      settingsItems.value[0].items.shift()
      appsMenuIndex--
    } else
      settingsItems.value[0].items[0].submenu = teams.map(([k, v]) => ({
        label: v.title,
        onClick: () => {
          router.push({ name: "Home", params: { team: k } })
          LISTS.forEach((l) => l.reset())
        },
      }))

    settingsItems.value[0].items[appsMenuIndex].submenu = a.map((app) => ({
      label: app.title,
      icon: app.logo,
      component: h(
        "a",
        {
          class:
            "flex items-center gap-2 p-1.5 rounded hover:bg-surface-gray-2",
          href: app.route,
        },
        [
          h("img", { src: app.logo, class: "size-6" }),
          h("span", { class: "max-w-18 text-sm w-full truncate" }, app.title),
        ]
      ),
    }))
  },
  { immediate: true }
)
// const settingsItems = computed(() => {
//   return [
//     {
//       group: __("Manage"),
//       hideLabel: true,
//       items: [
//         {
//           component: markRaw(TeamSwitcher),
//         },
//         {
//           component: markRaw(AppSwitcher),
//         },
//         {
//           icon: LucideBook,
//           label: __("Documentation"),
//           onClick: () => window.open("https://docs.frappe.io/drive", "_blank"),
//         },
//         {
//           icon: LucideBadgeHelp,
//           label: __("Support"),
//           onClick: () => window.open("https://t.me/frappedrive", "_blank"),
//         },
//         {
//           icon: LucideMoon,
//           label: "Toggle theme",
//           onClick: toggleTheme,
//         },
//       ],
//     },
//     {
//       group: __("Others"),
//       hideLabel: true,
//       items: [
//         {
//           icon: "settings",
//           label: __("Settings"),
//           onClick: () => (showSettings.value = true),
//         },
//         {
//           icon: "log-out",
//           label: __("Log out"),
//           onClick: logout,
//         },
//       ],
//     },
//   ]
// })

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme")
  let theme = currentTheme === "dark" ? "light" : "dark"
  document.documentElement.setAttribute("data-theme", theme)
  localStorage.setItem("theme", theme)
}

onMounted(() => {
  const theme = localStorage.getItem("theme")
  if (["light", "dark"].includes(theme)) {
    document.documentElement.setAttribute("data-theme", theme)
  }
})

function logout() {
  store.dispatch("logout")
  router.redirect("/")
}
const sidebarItems = computed(() => {
  const first = store.state.breadcrumbs[0]
  return [
    {
      items: [
        {
          label: __("Find"),
          icon: LucideSearch,
          onClick: () => emitter.emit("showSearchPopup", true),
        },
        {
          label: __("Inbox"),
          icon: LucideInbox,
          to: "/t/" + team.value + "/inbox",
          isActive: first.name === "Inbox",
        },
      ],
    },
    {
      label: "Drive",
      items: [
        {
          label: "Home",
          to: `/t/${team.value}/`,
          icon: LucideHome,
          isActive: first.name == "Home",
        },

        {
          label: "Team",
          to: `/t/${team.value}/team`,
          icon: LucideBuilding2,
          isActive: first.name == "Team",
        },

        {
          label: "Trash",
          to: `/t/${team.value}/trash`,
          icon: LucideTrash,
          isActive: first.name == "Trash",
        },
      ],
    },
    {
      label: "Views",
      collapsible: true,
      items: [
        {
          label: "Recents",
          to: `/t/${team.value}/recents`,
          icon: LucideClock,
          isActive: first.name == "Recents",
        },
        {
          label: "Shared",
          to: `/shared/`,
          icon: LucideUsers,
          isActive: first.name == "Shared",
        },

        {
          label: "Favourites",
          to: `/t/${team.value}/favourites`,
          icon: LucideStar,
          isActive: first.name == "Favourites",
        },
        {
          label: "Documents",
          to: `/t/${team.value}/documents`,
          icon: LucideFileText,
          isActive: first.name == "Documents",
        },
      ],
    },
  ]
})

watch(isCollapsed, (val) => store.commit("setSidebarCollapsed", val))
</script>
