<template>
  <GenericPage
    :getEntities="getFavourites"
    :icon="Star"
    :primaryMessage="'No Favourite Files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Star from "../components/EspressoIcons/Star.vue"
import { getFavourites } from "@/resources/files"
</script>
