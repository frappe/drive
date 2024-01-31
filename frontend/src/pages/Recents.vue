<template>
  <PageGeneric
    url="drive.api.files.list_recents"
    :allowEmptyContextMenu="false"
    :showSort="false"
    :primary-message="`You haven't viewed any files recently`"
    :secondary-message="'Files will appear here for easy access when you view them sorted by last interaction'" />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue";
</script>
