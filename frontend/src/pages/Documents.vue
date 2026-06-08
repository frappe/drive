<template>
  <GenericPage
    :get-entities="getDocuments"
    :icon="LucideFileText"
    :empty="{
      icon: LucideFileText,
      title: 'No documents yet',
      description: `Use Writer to create documents.`,
    }"
  />
</template>
<script setup>
import GenericPage from '@/components/GenericPage.vue'
import LucideFileText from '~icons/lucide/file-text'
import { getDocuments } from '@/resources/files'
</script>
