<template>
  <GenericPage
    :get-entities="getHome"
    :icon="Home"
    :primary-message="'Home is empty'"
    :secondary-message="'Add files by dropping them here'"
  />
</template>

<script setup>
import Home from "../components/EspressoIcons/Home.vue"
import GenericPage from "@/components/GenericPage.vue"
import { getHome } from "@/resources/files"
</script>
