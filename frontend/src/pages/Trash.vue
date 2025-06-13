<template>
  <GenericPage
    :getEntities="getTrash"
    :icon="LucideTrash"
    primaryMessage="Trash is empty"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getTrash } from "@/resources/files"
import { LucideTrash } from "lucide-vue-next"
</script>
