<template>
  <GenericPage
    :getEntities="getPersonal"
    :icon="MyDrive"
    :primaryMessage="'No personal files'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import MyDrive from "../components/EspressoIcons/MyDrive.vue"
import { getPersonal } from "@/resources/files"
</script>
