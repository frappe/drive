<template>
  <GenericPage
    :getEntities="getSlides"
    :icon="LucideFileText"
    primary-message="You haven't created any slides yet."
  />
</template>
<script setup>
import GenericPage from "@/components/GenericPage.vue"
import LucideFileText from "~icons/lucide/file-text"
import { getSlides } from "@/resources/files"
</script>
