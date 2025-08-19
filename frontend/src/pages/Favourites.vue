<template>
  <GenericPage
    :get-entities="getFavourites"
    :icon="LucideStar"
    :primary-message="__('No favourites yet')"
    :secondary-message="__('Click on the star icon to favourite an item.')"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue";
import { getFavourites } from "@/resources/files";
import LucideStar from "~icons/lucide/star";
</script>
