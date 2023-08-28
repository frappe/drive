<template>
  <Dropdown
    :options="[
      {
        icon: 'settings',
        label: 'Settings',
        onClick: () => (showSettings = true),
      },
      {
        icon: 'log-out',
        label: 'Log out',
        onClick: () => logout(),
      },
    ]">
    <template v-slot="{ open }">
      <button
        class="flex w-full items-center space-x-2 rounded-md p-2 text-left"
        :class="open ? 'bg-gray-300' : 'hover:bg-gray-200'">
        <Avatar :image="imageURL" :label="fullName" size="md" />
        <span class="hidden text-base font-medium text-gray-900 sm:inline">
          {{ firstName[0] }}
        </span>
        <FeatherIcon name="chevron-down" class="hidden h-4 w-4 sm:inline" />
      </button>
    </template>
  </Dropdown>
  <Settings v-if="showSettings" v-model="showSettings" />
</template>
<script>
import { Dropdown, FeatherIcon, Avatar } from "frappe-ui";
import Settings from "@/components/Settings.vue";

export default {
  name: "UserDropdown",
  components: {
    Dropdown,
    FeatherIcon,
    Avatar,
    Settings,
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
    firstName() {
      return this.$store.state.user.fullName.split(" ");
    },
    fullName() {
      return this.$store.state.user.fullName;
    },
    imageURL() {
      return this.$store.state.user.imageURL;
    },
  },
};
</script>
