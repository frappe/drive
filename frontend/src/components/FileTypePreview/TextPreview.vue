<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full z-10 text-neutral-100 mx-auto"
  />
  <div
    v-else
    id="container"
    class="flex items-center justify-center w-full h-full overflow-auto"
  >
    <pre
      class="bg-gray-50 sm:w-full md:w-2/3 h-[85vh] text-gray-800 text-sm border select-text p-3 font-mono overflow-x-auto overflow-y-auto"
      >{{ blob }}</pre
    >
  </div>
</template>

<script setup>
/* Consider adding https://codemirror.net/ and add a mimetype eval list for all possible mimetypes */

import { LoadingIndicator } from "frappe-ui"
import { onMounted, ref, watch } from "vue"

const props = defineProps({
  previewEntity: {
    type: String,
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
<style scoped></style>
