<template>
  <GenericPage
    :getEntities="getPersonal"
    :icon="Star"
    :primaryMessage="'No personal files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Star from "../components/EspressoIcons/Star.vue"
import { getPersonal } from "@/resources/files"
</script>
