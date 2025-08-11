<template>
  <GenericPage
    :getEntities="getDocuments"
    :icon="LucideFileText"
    primary-message="You haven't created documents yet."
  />
</template>
<script setup>
import GenericPage from "@/components/GenericPage.vue"
import { createResource, toast } from "frappe-ui"
import LucideFileText from "~icons/lucide/file-text"
import { COMMON_OPTIONS } from "@/resources/files"
import { onMounted } from "vue"

onMounted(() => {
  toast.success("Co pied to clipboard")
})
const getDocuments = createResource({
  ...COMMON_OPTIONS,
  url: "drive.api.list.files",
  makeParams: (params) => {
    return { ...params, file_kinds: '["Frappe Document"]' }
  },
  cache: "document-folder-contents",
})
</script>
