<template>
  <Dropdown
    :options="[
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
        <Avatar :imageURL="imageURL" :label="fullName" size="md" />
        <span class="hidden text-base font-medium text-gray-900 sm:inline">
          {{ fullName }}
        </span>
        <LucideChevronDown class="hidden h-4 w-4 sm:inline" />
      </button>
    </template>
  </Dropdown>
</template>
<script>
import { Dropdown, Link, Avatar } from "frappe-ui";

export default {
  name: "UserDropdown",
  components: {
    Dropdown,
    Link,
    Avatar,
  },
  methods: {
    logout() {
      this.$session.logout.submit();
    },
  },
  computed: {
    fullName() {
      return this.$store.state.user.fullName;
    },
    imageURL() {
      return this.$store.state.user.imageURL;
    },
  },
};
</script>
