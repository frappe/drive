<template>
  <GenericPage
    :getEntities="getTrash"
    :icon="Trash"
    :primaryMessage="'Trash is Empty'"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import Trash from "../components/EspressoIcons/Trash.vue"
import { getTrash } from "@/resources/files"
</script>
