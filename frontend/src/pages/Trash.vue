<template>
  <PageGeneric
    url="drive.api.files.list_trashed_entities"
    :allow-empty-context-menu="false"
    :is-active="false"
    :show-sort="true"
    :primary-message="`Trash is currently empty`"
    :secondary-message="'Items in the trash will be deleted automatically after 30 days'"
  />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue"
</script>
