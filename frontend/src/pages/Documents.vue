<template>
  <GenericPage
    :get-entities="getDocuments"
    :icon="LucideFileText"
    :empty="{
      icon: LucideFileText,
      title: `Nothing here`,
      description: `You haven't created documents yet.`,
    }"
  />
</template>
<script setup>
import GenericPage from "@/components/GenericPage.vue"
import LucideFileText from "~icons/lucide/file-text"
import { getDocuments } from "@/resources/files"
</script>
