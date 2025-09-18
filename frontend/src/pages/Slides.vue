<template>
  <GenericPage
    :getEntities="getSlides"
    :empty="{
      icon: LucideGalleryVerticalEnd,
      title: 'No presentations yet.',
    }"
  />
</template>
<script setup>
import GenericPage from "@/components/GenericPage.vue"
import LucideGalleryVerticalEnd from "~icons/lucide/gallery-vertical-end"
import { getSlides } from "@/resources/files"
</script>
