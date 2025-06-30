<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10"
  />
  <pre
    v-else
    class="font-[InterVar] font-normal text-p-base text-ink-gray-8 sm:w-full md:w-2/3 mx-auto border p-3 rounded overflow-x-auto"
  >
      {{ blob }}
    </pre
  >
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
<style scoped></style>
