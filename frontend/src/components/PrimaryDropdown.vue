<template>
  <Dropdown :options="settingsItems">
    <template #default="{ open }">
      <button
        class="flex items-center justify-center rounded-md text-left"
        :class="[
          isExpanded ? 'p-2' : '',
          open ? 'bg-white shadow-sm' : 'hover:bg-gray-200',
        ]"
        :style="{
          width: isExpanded ? '204px' : 'auto',
        }">
        <FrappeDriveLogo class="w-8 h-8 rounded" />
        <div v-if="isExpanded" class="ml-2 flex flex-col">
          <div class="text-base font-medium text-gray-900 leading-none">
            Frappe Drive
          </div>
          <div class="mt-1 hidden text-sm text-gray-700 sm:inline leading-none">
            {{ userEmail }}
          </div>
        </div>
        <FeatherIcon
          v-if="isExpanded"
          :name="open ? 'chevron-up' : 'chevron-down'"
          class="ml-auto hidden h-5 w-5 sm:inline text-gray-700" />
      </button>
    </template>
  </Dropdown>
  <Settings v-if="showSettings" v-model="showSettings" />
</template>
<script>
import { Dropdown, FeatherIcon } from "frappe-ui";
import Settings from "@/components/Settings.vue";
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue";

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
      return this.$store.state.user.fullName.split(" ");
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    userEmail() {
      return this.$store.state.auth.user_id;
    },
    settingsItems() {
      return [
        {
          icon: "grid",
          label: "Switch to Desk",
          condition: () => this.$store.state.user.isSystemUser,
          onClick() {
            window.location.href = "/app";
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
      ];
    },
  },
  methods: {
    logout() {
      this.$store.dispatch("logout");
    },
  },
};
</script>
