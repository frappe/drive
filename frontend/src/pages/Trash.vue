<template>
  <GenericPage
    :get-entities="getTrash"
    :icon="LucideTrash"
    primary-message="Trash is empty"
    secondary-message="Trashed files will show up here - you can restore them."
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getTrash } from "@/resources/files"
import LucideTrash from "~icons/lucide/trash"
</script>
