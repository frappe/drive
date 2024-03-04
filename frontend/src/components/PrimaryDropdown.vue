<template>
  <Dropdown :options="settingsItems">
    <template v-slot="{ open }">
      <button
        class="flex items-center rounded-md text-left ml-[1px] px-3 py-1.5 hover:bg-gray-200"
        :style="{
          width: isExpanded ? '250px' : 'auto',
        }">
        <Avatar :image="imageURL" size="xl" :label="fullName" />
        <div v-if="isExpanded" class="ml-2 flex flex-col">
          <div class="text-base font-medium text-gray-900 leading-none">
            {{ fullName }}
          </div>
          <div class="mt-1 hidden text-sm text-gray-700 sm:inline leading-none">
            {{ isAdmin ? "Drive Admin" : "Drive User" }}
          </div>
        </div>
        <FeatherIcon
          v-if="isExpanded"
          name="chevron-up"
          class="ml-auto hidden h-4 w-4 sm:inline" />
      </button>
    </template>
  </Dropdown>
  <Settings v-if="showSettings" v-model="showSettings" />
</template>
<script>
import { Dropdown, FeatherIcon, Avatar } from "frappe-ui";
import Settings from "@/components/Settings.vue";
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue";

export default {
  name: "PrimaryDropdown",
  components: {
    Dropdown,
    FeatherIcon,
    Avatar,
    Settings,
    FrappeDriveLogo,
    Avatar,
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
            icon: "grid",
            label: "Switch to Desk",
            route: "/workspace",
            highlight: () => {
              return this.$route.fullPath.endsWith("/workspace");
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
