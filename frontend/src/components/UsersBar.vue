<template>
  <button class="ml-2.5 flex justify-center items-center rounded-md">
    <div
      class="-ml-2.5 py-0.5 flex items-center rounded-full"
      v-for="user in connectedUsers">
      <Avatar
        :size="'md'"
        :style="{
          border: '2px solid',
          borderRadius: '100%',
          borderColor: user.color,
        }"
        :label="user.name" />
    </div>
  </button>
</template>

<script>
import { Avatar } from "frappe-ui";

export default {
  name: "UsersBar",
  components: {
    Avatar,
  },
  computed: {
    connectedUsers() {
      return this.$store.state.connectedUsers;
    },
  },
};
</script>
