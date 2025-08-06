<template>
  <GenericPage
    :getEntities="getDocuments"
    :icon="LucideFileText"
    primary-message="You haven't created documents yet."
  />
</template>
<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { createResource } from "frappe-ui"
import LucideFileText from "~icons/lucide/file-text"
import { COMMON_OPTIONS } from "@/resources/files"

const getDocuments = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => {
    return { ...params, file_kinds: '["Frappe Document"]' }
  },
  cache: "document-folder-contents",
})
</script>
