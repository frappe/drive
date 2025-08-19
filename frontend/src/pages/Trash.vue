<template>
  <GenericPage
    :get-entities="getTrash"
    :icon="LucideTrash"
    primary-message="Thùng rác trống"
  />
</template>

<script setup>
import GenericPage from "@/components/GenericPage.vue";
import { getTrash } from "@/resources/files";
import LucideTrash from "~icons/lucide/trash";
</script>
