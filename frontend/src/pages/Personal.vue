<template>
  <GenericPage
    :get-entities="getPersonal"
    :icon="Home"
    primary-message="No personal files"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Home from "../components/EspressoIcons/Home.vue"
import { getPersonal } from "@/resources/files"
</script>
