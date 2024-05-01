<template>
  <button
    class="flex items-center rounded-md text-left m-2"
    :style="{
      width: isExpanded ? '200px' : 'auto',
    }"
    @click="() => $router.push({ name: 'Home' })"
  >
    <FrappeDriveLogo class="w-8 h-8 rounded" />
    <div v-if="isExpanded" class="ml-2 flex flex-col">
      <div class="text-base font-medium text-gray-900 leading-none">
        Frappe Drive
      </div>
    </div>
  </button>
  <Settings v-if="showSettings" v-model="showSettings" />
</template>
<script>
import Settings from "@/components/Settings.vue"
import FrappeDriveLogo from "@/components/FrappeDriveLogo.vue"

export default {
  name: "UserDropdown",
  components: {
    Settings,
    FrappeDriveLogo,
  },
  data: () => ({
    showSettings: false,
  }),
  computed: {
    isExpanded() {
      return this.$store.state.IsSidebarExpanded
    },
    firstName() {
      return this.$store.state.user.fullName.split(" ")
    },
    fullName() {
      return this.$store.state.user.fullName
    },
    imageURL() {
      return this.$store.state.user.imageURL
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
        ]
      }
      return [
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
            this.errorMessage = error.messages.join("\n")
          } else {
            this.errorMessage = error.message
          }
        },
        auto: true,
      }
    },
  },
}
</script>
