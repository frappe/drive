<template>
  <PageGeneric
    url="drive.api.files.list_trashed_entities"
    :allowEmptyContextMenu="false"
    :isActive="false"
    :showSort="true"
    :primary-message="`Trash is currently empty`"
    :secondary-message="'Items in the trash will be deleted automatically after 30 days'" />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue";
</script>
