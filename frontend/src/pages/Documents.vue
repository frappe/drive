<template>
  <GenericPage
    :getEntities="getDocuments"
    :icon="LucideFileText"
    :empty="{
      icon: LucideFileText,
      title: `Nothing here`,
      description: `You haven't created documents yet.`,
    }"
    primary-message=""
  />
</template>
<script setup>
import GenericPage from "@/components/GenericPage.vue"
import LucideFileText from "~icons/lucide/file-text"
import LucidePlus from "~icons/lucide/plus"
import { getDocuments } from "@/resources/files"
import { h } from "vue"
</script>
