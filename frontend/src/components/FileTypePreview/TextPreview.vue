<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10"
  />
    <div
    v-else
    class="w-full text-preview-container"
  >
    <pre
      class="max-h-[80vh] overflow-y-auto font-[InterVar] font-normal text-p-base sm:w-full border p-3 rounded overflow-x-auto text-preview"
    >{{ blob }}</pre>
  </div>
</template>

<script setup>
/* Consider adding https://codemirror.net/ and add a mimetype eval list for all possible mimetypes */

import { LoadingIndicator } from "frappe-ui"
import { onMounted, ref, watch } from "vue"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: "",
  },
})

const loading = ref(true)
const blob = ref(null)

async function fetchContent() {
  loading.value = true
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
    Range: "bytes=0-10000000",
  }
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    {
      method: "GET",
      headers,
    }
  )
  if (res.ok) {
    let resBlob = await res.blob()
    blob.value = await resBlob.text()
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
</script>
<style scoped>
.text-preview-container {
  width: 100% !important;
  max-width: 100% !important;
  height: fit-content !important;
  align-self: flex-start !important;
  flex: none !important;
  /* Ensure container takes up appropriate space */
  display: block !important;
}

.text-preview {
  color: #383838 !important;
  background-color: #ffffff !important;
  /* Ensure proper display properties */
  display: block !important;
  width: 100% !important;
  min-height: fit-content !important;
  height: fit-content !important;
  /* Ensure text remains visible at all zoom levels */
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /* Force color inheritance and prevent zoom-related color issues */
  forced-color-adjust: none;
  /* Prevent any color override */
  -webkit-text-fill-color: #383838 !important;
  /* Reset any inherited flex properties */
  flex: none !important;
}

/* Ensure readability in dark mode or high contrast scenarios */
@media (prefers-color-scheme: dark) {
  .text-preview {
    color: #d1d5db !important;
    background-color: #1f2937 !important;
    -webkit-text-fill-color: #d1d5db !important;
  }
}

/* Ensure text visibility at high zoom levels */
@media (min-resolution: 2dppx) {
  .text-preview {
    font-weight: 400 !important;
  }
}

/* Override any inherited text colors */
.text-preview * {
  color: inherit !important;
}
</style>