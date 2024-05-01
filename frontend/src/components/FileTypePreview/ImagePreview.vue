<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <img v-else draggable="false" class="w-auto max-h-full" :src="previewURL" />
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui"
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useObjectUrl } from "@vueuse/core"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
  },
})

const loading = ref(true)
const imgBlob = ref(null)
const previewURL = useObjectUrl(imgBlob)

watch(props.previewEntity, () => {
  loading.value = true
  imgBlob.value = null
  fetchContent()
})

async function fetchContent() {
  loading.value = true
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
  }
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    {
      method: "GET",
      headers,
    }
  )
  if (res.ok) {
    imgBlob.value = await res.blob()
    loading.value = false
  }
}

watch(
  () => props.previewEntity,
  () => {
    fetchContent()
  }
)

onMounted(() => {
  fetchContent()
})

onBeforeUnmount(() => {
  loading.value = true
  imgBlob.value = null
})
</script>

<style scoped>
img {
  background-image: linear-gradient(45deg, #ccc 25%, transparent 25%),
    linear-gradient(135deg, #ccc 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #ccc 75%),
    linear-gradient(135deg, white 75%, #ccc 75%);
  background-size: 30px 30px; /* Must be a square */
  background-position: 0 0, 15px 0, 15px -15px, 0px 15px; /* Must be half of one side of the square */
}
</style>
