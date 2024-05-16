<template>
  <PageGeneric
    url="drive.api.files.list_trashed_entities"
    :allow-empty-context-menu="false"
    :is-active="false"
    :show-sort="true"
    :icon="Trash"
    :primaryMessage="'Trash is Empty'"
    :secondaryMessage="''"
  />
</template>

<script setup>
import PageGeneric from "@/components/PageGeneric.vue"
import Trash from "../components/EspressoIcons/Trash.vue"
</script>
