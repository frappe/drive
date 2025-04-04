<template>
  <Dropdown :options="settingsItems">
    <template #default="{ open }">
      <button
        class="flex items-center justify-start rounded-md text-left transition-all duration-300 ease-in-out"
        :class="[
          isExpanded ? 'p-2' : 'py-2',
          open && isExpanded
            ? 'bg-white shadow-sm'
            : isExpanded
            ? 'hover:bg-gray-200'
            : 'bg-transparent hover:bg-transparent shadow-none',
        ]"
        :style="{
          width: isExpanded ? '204px' : 'auto',
        }"
      >
        <FrappeDriveLogo class="w-8 h-8 rounded" />
        <div
          class="flex flex-1 flex-col text-left duration-300 text-nowrap ease-in-out"
          :class="
            isExpanded
              ? 'ml-2 w-auto opacity-100'
              : 'ml-0 w-0 opacity-0 overflow-hidden'
          "
        >
          <div class="text-base font-medium leading-none text-gray-900">
            {{ teamName }}
          </div>
          <div
            class="line-clamp-1 overflow-hidden text-sm leading-none text-gray-700"
            :class="teamName ? 'mt-1' : 'mb-1'"
          >
            {{ fullName }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            isExpanded
              ? 'mr-auto w-auto opacity-100'
              : 'ml-0 w-0 overflow-hidden opacity-0'
          "
        >
          <FeatherIcon
            :name="open ? 'chevron-up' : 'chevron-down'"
            class="h-5 w-5 sm:inline text-gray-700"
          />
        </div>
      </button>
    </template>
  </Dropdown>
  <SettingsDialog
    v-if="showSettings"
    v-model="showSettings"
    :suggested-tab="suggestedTab"
  />
</template>

<script setup>
import { markRaw, onMounted } from "vue"
import { Dropdown, FeatherIcon } from "frappe-ui"
import SettingsDialog from "@/components/Settings/SettingsDialog.vue"
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"
import Docs from "@/components/EspressoIcons/Docs.vue"
import AppSwitcher from "@/components/AppSwitcher.vue"
import TeamSwitcher from "@/components/TeamSwitcher.vue"
import { getTeams } from "@/resources/files"
import emitter from "@/emitter"
import { ref, computed, watch } from "vue"
import { useStore } from "vuex"
import { useRouter, useRoute } from "vue-router"

const router = useRouter()
const route = useRoute()
const team = computed(() => route.params?.team)
const teamName = ref("loading...")
watch(
  team,
  async (v) => {
    if (!v) return
    if (!getTeams.data) await getTeams.fetch()
    teamName.value = getTeams.data[v]?.title
  },
  { immediate: true }
)
const store = useStore()

defineProps({
  isExpanded: Boolean,
})
const showSettings = ref(false)
const suggestedTab = ref(0)

const fullName = computed(() => store.state.user.fullName)

const settingsItems = computed(() => {
  return [
    {
      group: "Manage",
      hideLabel: true,
      items: [
        {
          component: markRaw(TeamSwitcher),
        },
        {
          icon: Docs,
          label: "Documentation",
          onClick: () => window.open("https://docs.frappe.io/drive", "_blank"),
        },
        {
          icon: "life-buoy",
          label: "Support",
          onClick: () => window.open("https://t.me/frappedrive", "_blank"),
        },
      ],
    },
    {
      group: "Others",
      hideLabel: true,
      items: [
        {
          icon: "settings",
          label: "Settings",
          onClick: () => (showSettings.value = true),
        },
        {
          icon: "log-out",
          label: "Log out",
          onClick: logout,
        },
      ],
    },
  ]
})

emitter.on("showSettings", (val) => {
  showSettings.value = true
  suggestedTab.value = val || 0
})

function logout() {
  store.dispatch("logout")
  router.redirect("/")
}
</script>
