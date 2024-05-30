<template>
  <h1 class="font-semibold mb-6">Members</h1>
  <UserListSettings />
  <UserRoleSettings />
</template>
<script setup>
import UserListSettings from "./UserListSettings.vue"
import UserRoleSettings from "./UserRoleSettings.vue"
import { createResource } from "frappe-ui"
import { useStore } from "vuex"

const store = useStore()
createResource({
  url: "drive.utils.users.is_drive_admin",
  method: "POST",
  auto: true,
  onSuccess(data) {
    store.state.user.driveAdmin = data
  },
})
</script>
