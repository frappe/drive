<template>
  <PageGeneric
    url="drive.api.files.list_recents"
    :allow-empty-context-menu="false"
    :show-sort="false"
    :icon="Recent"
    primary-message="No Recent Files"
    :secondary-message="''"
  />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue"
import Recent from "../components/EspressoIcons/Recent.vue"
</script>
