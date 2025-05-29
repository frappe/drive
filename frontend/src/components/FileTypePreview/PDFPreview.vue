<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full text-neutral-100 mx-auto absolute"
  />
  <embed
    ref="embed"
    :src="`/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`"
    type="application/pdf"
    class="w-4/5 h-full py-5"
    :class="{ 'opacity-0': loading }"
  />
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui"
import { onMounted, ref } from "vue"

const loading = ref(true)
const props = defineProps({
  previewEntity: Object,
})

onMounted(() => {
  setTimeout(() => (loading.value = false), 1000)
})
</script>
