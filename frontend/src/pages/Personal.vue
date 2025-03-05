<template>
  <GenericPage
    :getEntities="getPersonal"
    :icon="Home"
    :primaryMessage="'No personal files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Home from "../components/EspressoIcons/Home.vue"
import { getPersonal } from "@/resources/files"
</script>
