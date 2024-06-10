<template>
  <div
    id="DocxContainer"
    class="object-contain h-[85vh] max-w-[65vw] z-10 overflow-y-auto rounded border"
  ></div>
</template>
<script setup>
import * as docx from "docx-preview"
import { onBeforeUnmount, onMounted, ref, watch } from "vue"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
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
    blob.value = await res.blob()
    docx.renderAsync(
      blob.value,
      document.getElementById("DocxContainer"),
      document.getElementById("DocxContainer"),
      {
        ignoreLastRenderedPageBreak: false,
        experimental: true,
      }
    )
    //.then((x) => console.log("docx: finished"));
    loading.value = false
  }
}

onMounted(() => {
  fetchContent()
})

watch(
  () => props.previewEntity,
  () => {
    fetchContent()
  }
)

onBeforeUnmount(() => {
  loading.value = true
  blob.value = null
})
</script>

<style>
#DocxContainer {
  user-select: text;
}
</style>
