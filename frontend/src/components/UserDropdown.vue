<template>
  <button
    @click="() => $router.push({ name: 'Home' })"
    class="flex items-center rounded-md text-left px-3 mt-2"
    :style="{
      width: isExpanded ? '250px' : 'auto',
    }">
    <FrappeDriveLogo class="w-8.5 h-8.5 rounded" />
    <div v-if="isExpanded" class="ml-2 flex flex-col">
      <div class="text-base font-medium text-gray-900 leading-none">
        Frappe Drive
      </div>
    </div>
  </button>
  <Settings v-if="showSettings" v-model="showSettings" />
</template>
<script>
import { Dropdown, FeatherIcon, Avatar } from "frappe-ui";
import Settings from "@/components/Settings.vue";
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue";

export default {
  name: "UserDropdown",
  components: {
    Dropdown,
    FeatherIcon,
    Avatar,
    Settings,
    FrappeDriveLogo,
  },
  data: () => ({
    showSettings: false,
  }),
  methods: {
    logout() {
      this.$store.dispatch("logout");
    },
  },
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded;
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ");
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    imageURL() {
      return this.$store.state.user.imageURL;
    },
    settingsItems() {
      if (this.$resources.isAdmin?.data) {
        return [
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
      }
      return [
        {
          icon: "log-out",
          label: "Log out",
          onClick: () => this.logout(),
        },
      ];
    },
  },
  resources: {
    isAdmin() {
      return {
        url: "drive.utils.users.is_drive_admin",
        cache: "is_admin",
        params: {
          doctype: "Drive Instance Settings",
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
        auto: true,
      };
    },
  },
};
</script>
