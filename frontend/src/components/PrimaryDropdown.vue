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
          //open && isExpanded ? 'hover:bg-transparent' : 'bg-transparent hover:bg-transparent',
        ]"
        :style="{
          width: isExpanded ? '204px' : 'auto',
        }"
      >
        <FrappeDriveLogo class="w-8 h-8 rounded" />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out"
          :class="isExpanded ? 'ml-2 w-auto opacity-100' : 'ml-0 w-0 opacity-0'"
        >
          <div class="text-base font-medium leading-none text-gray-900">
            Drive
          </div>
          <div
            class="line-clamp-1 overflow-hidden mt-1 text-sm leading-none text-gray-700"
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
<script>
import { Dropdown, FeatherIcon } from "frappe-ui"
import SettingsDialog from "@/components/Settings/SettingsDialog.vue"
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"
import Docs from "@/components/EspressoIcons/Docs.vue"

export default {
  name: "PrimaryDropdown",
  components: {
    Dropdown,
    FeatherIcon,
    SettingsDialog,
    FrappeDriveLogo,
  },
  props: {
    isExpanded: Boolean,
  },
  data: () => ({
    showSettings: false,
    suggestedTab: 0,
  }),
  computed: {
    firstName() {
      return this.$store.state.user.fullName.split(" ")
    },
    fullName() {
      return this.$store.state.user.fullName
    },
    userEmail() {
      return this.$store.state.auth.user_id
    },
    settingsItems() {
      return [
        {
          group: "Manage",
          hideLabel: true,
          items: [
            {
              icon: "corner-up-left",
              label: "Switch to Desk",
              condition: () => this.$store.state.user.systemUser,
              onClick() {
                window.location.href = "/app"
              },
            },
            {
              icon: Docs,
              label: "Documentation",
              onClick: () =>
                window.open("https://docs.frappe.io/drive", "_blank"),
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
              onClick: () => (this.showSettings = true),
            },
            {
              icon: "log-out",
              label: "Log out",
              onClick: () => this.logout(),
            },
          ],
        },
      ]
    },
  },
  mounted() {
    this.emitter.on("showSettings", (val) => {
      this.showSettings = true
      this.suggestedTab = val
    })
  },
  methods: {
    logout() {
      this.$store.dispatch("logout")
    },
  },
}
</script>
