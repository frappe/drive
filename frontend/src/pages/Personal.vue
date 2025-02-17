<template>
  <GenericPage
    :getEntities="getPersonal"
    :icon="Lock"
    :primaryMessage="'No personal files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Lock from "../components/EspressoIcons/Lock.vue"
import { getPersonal } from "@/resources/files"
</script>
