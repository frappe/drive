<template>
  <PageGeneric
    url="drive.api.list.files"
    :favourites="true"
    :allow-empty-context-menu="false"
    :show-sort="true"
    :icon="Star"
    :primaryMessage="'No Favourite Files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue"
import Star from "../components/EspressoIcons/Star.vue"
</script>
