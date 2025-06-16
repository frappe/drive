<template>
  <GenericPage
    :get-entities="getTrash"
    :icon="LucideTrash"
    primary-message="Trash is empty"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getTrash } from "@/resources/files"
import { LucideTrash } from "lucide-vue-next"
</script>
