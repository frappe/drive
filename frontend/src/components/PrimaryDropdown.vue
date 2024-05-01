<template>
  <Dropdown :options="settingsItems">
    <template #default="{ open }">
      <button
        class="flex items-center justify-start rounded-md text-left transition-all duration-300 ease-in-out"
        :class="[
          isExpanded ? 'p-2' : 'py-2',
          open ? 'bg-white shadow-sm' : 'hover:bg-gray-200',
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
  <Settings v-if="showSettings" v-model="showSettings" />
</template>
<script>
import { Dropdown, FeatherIcon } from "frappe-ui"
import Settings from "@/components/Settings.vue"
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"

export default {
  name: "PrimaryDropdown",
  components: {
    Dropdown,
    FeatherIcon,
    Settings,
    FrappeDriveLogo,
  },
  props: {
    isExpanded: Boolean,
  },
  data: () => ({
    showSettings: false,
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
          icon: "grid",
          label: "Switch to Desk",
          condition: () => this.$store.state.user.isSystemUser,
          onClick() {
            window.location.href = "/app"
          },
        },
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
      ]
    },
  },
  methods: {
    logout() {
      this.$store.dispatch("logout")
    },
  },
}
</script>
