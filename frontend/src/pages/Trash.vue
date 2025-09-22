<template>
  <GenericPage
    :get-entities="getTrash"
    :empty="{
      icon: LucideTrash,
      title: 'Trash is empty',
      description: 'Trashed files will show up here - you can restore them.',
    }"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { getTrash } from "@/resources/files"
import LucideTrash from "~icons/lucide/trash"
</script>
