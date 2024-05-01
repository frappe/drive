<template>
  <PageGeneric
    url="drive.api.files.list_favourites"
    :allow-empty-context-menu="false"
    :show-sort="true"
    :primary-message="`You haven't favourited any items`"
    :secondary-message="'Items will appear here for easy access when you add them to favourites'"
  />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue"
</script>
