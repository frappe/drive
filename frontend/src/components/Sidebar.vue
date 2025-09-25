<template>
  <Sidebar
    v-model:collapsed="isCollapsed"
    id="sidebar"
    class="hidden sm:flex"
    :header="{
      title: 'Drive',
      subtitle: $store.state.user.fullName,
      menuItems: settingsItems,
      logo: FrappeDriveLogo,
    }"
    :sections="sidebarItems"
  >
    <template #footer-items="{ isCollapsed }">
      <StorageBar
        v-if="teamExists.data"
        :is-expanded="!isCollapsed"
      />
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

import { notifCount, apps } from "@/resources/permissions"
import { getTeams, LISTS } from "@/resources/files"
import { dynamicList } from "@/utils/files"

import { useStore } from "vuex"
import icons from "@/utils/icons"
import LucideClock from "~icons/lucide/clock"
import LucideUsers from "~icons/lucide/users"
import LucideTrash from "~icons/lucide/trash"
import LucideHome from "~icons/lucide/home"
import LucideStar from "~icons/lucide/star"
import LucideInbox from "~icons/lucide/inbox"
import LucideSearch from "~icons/lucide/search"
import LucideFileText from "~icons/lucide/file-text"
import LucideGalleryVerticalEnd from "~icons/lucide/gallery-vertical-end"

import SettingsDialog from "@/components/Settings/SettingsDialog.vue"
import ShortcutsDialog from "@/components/ShortcutsDialog.vue"
import emitter from "@/emitter"
import { ref, computed, watch, shallowRef, onMounted, h } from "vue"
import AppsIcon from "@/components/AppsIcon.vue"
import { useRoute, useRouter } from "vue-router"

import LucideBook from "~icons/lucide/book"
import LucideBadgeHelp from "~icons/lucide/badge-help"
import LucideMoon from "~icons/lucide/moon"

defineEmits(["toggleMobileSidebar", "showSearchPopUp"])
const store = useStore()
const router = useRouter()
const route = useRoute()
notifCount.fetch()
getTeams.fetch()
apps.fetch()

const teamExists = createResource({
  url: "drive.utils.get_default_team",
  auto: true,
  onSuccess: (d) => {
    !d && router.replace({ name: "Setup" })
  },
})

const isCollapsed = ref(store.state.sidebarCollapsed)
watch(isCollapsed, (v) => store.commit("setSidebarCollapsed", v))
const team = computed(() => route.params.team)

const showSettings = ref(false)
const showShortcuts = ref(false)
const suggestedTab = ref(0)
emitter.on("showSettings", (val = 0) => {
  console.log(val)
  if (val === -1) showSettings.value = false
  else {
    showSettings.value = true
    suggestedTab.value = val
  }
})
emitter.on("toggleShortcuts", () => {
  showShortcuts.value = !showShortcuts.value
})

const settingsItems = computed(() => [
  {
    group: __("Manage"),
    hideLabel: true,
    items: [
      {
        icon: AppsIcon,
        label: __("Apps"),
        submenu: apps.data?.map?.((app) => ({
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
              h(
                "span",
                { class: "max-w-18 text-sm w-full truncate" },
                app.title
              ),
            ]
          ),
        })),
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
  const first = store.state.breadcrumbs[0] || {}
  return dynamicList([
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
          accessKey: "i",
        },
      ],
    },
    {
      label: "Drive",
      items: [
        {
          label: "Home",
          to: `/`,
          icon: LucideHome,
          isActive: first.name == "Home",
          accessKey: "h",
        },
        {
          label: "Recents",
          to: `/recents`,
          icon: LucideClock,
          isActive: first.name == "Recents",
          accessKey: "r",
        },
        {
          label: "Shared",
          to: `/shared`,
          icon: LucideUsers,
          isActive: first.name == "Shared",
          accessKey: "s",
        },
        {
          label: "Trash",
          to: `/trash`,
          icon: LucideTrash,
          isActive: first.name == "Trash",
        },
      ],
    },
    {
      label: "Teams",
      cond: getTeams.data && Object.keys(getTeams.data).length > 0,
      collapsible: true,
      items:
        getTeams.data &&
        Object.values(getTeams.data).map((team) => ({
          label: team.title,
          to: `/t/${team.name}/`,
          icon: h(icons[team.icon || "building"]),
          isActive: team.name === first.name,
          accessKey: "t",
        })),
    },
    {
      label: "Views",
      collapsible: true,
      items: dynamicList([
        {
          label: "Favourites",
          to: `/favourites`,
          icon: LucideStar,
          isActive: first.name == "Favourites",
          accessKey: "f",
        },
        {
          label: "Documents",
          to: `/documents`,
          icon: LucideFileText,
          isActive: first.name == "Documents",
          accessKey: "d",
        },
        {
          label: "Slides",
          to: `/presentations`,
          icon: LucideGalleryVerticalEnd,
          isActive: first.name == "Slides",
          cond: apps.data?.find?.((k) => k.name === "slides"),
        },
      ]),
    },
  ])
})
</script>
