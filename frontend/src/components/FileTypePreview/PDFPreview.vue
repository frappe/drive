<template>
  <embed
    :src="`/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`"
    type="application/pdf"
    class="w-screen h-screen border-none"
  />
</template>

<script setup>
const props = defineProps({
  previewEntity: Object,
})
</script>
