<template>
  {{}}
  <Tooltip :text="email">
    <span>{{ teamUsers.data.find((k) => k.name === email).full_name }}</span>
  </Tooltip>
</template>
<script setup>
import { teamUsers } from '@/resources/permissions'
import { Tooltip } from 'frappe-ui'
defineProps({
  email: String,
})
</script>
