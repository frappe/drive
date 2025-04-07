<template>
  <GenericPage
    :get-entities="getFavourites"
    :icon="Star"
    primary-message="No favourites yet"
    secondary-message="Click on the star icon to favourite an item."
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Star from "../components/EspressoIcons/Star.vue"
import { getFavourites } from "@/resources/files"
</script>
