<template>
  {{}}
  <Tooltip :text="email">
    <span>{{
      allUsers.data.find((k) => k.name === email).full_name
    }}</span>
  </Tooltip>
</template>
<script setup>
import { allUsers } from "@/resources/permissions"
import { Tooltip } from "frappe-ui"
defineProps({
  email: String,
})
</script>
