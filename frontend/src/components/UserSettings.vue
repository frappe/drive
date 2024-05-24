<template>
  <h1 class="font-semibold mb-8">Users</h1>
  <Tabs v-model="tabIndex" :tabs="tabs" tablist-class="pl-0">
    <template #default="{ tab }">
      <component :is="tab.component" />
    </template>
  </Tabs>
</template>
<script setup>
import { Tabs } from "frappe-ui"
import UserListSettings from "./UserListSettings.vue"
import UserRoleSettings from "./UserRoleSettings.vue"
import { ref } from "vue"
const tabIndex = ref()
const tabs = [
  {
    label: "Users",
    component: UserListSettings,
  },
  {
    label: "Groups",
    component: UserRoleSettings,
  },
]
</script>
