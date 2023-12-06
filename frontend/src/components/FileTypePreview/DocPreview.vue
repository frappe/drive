<template>
  <div
    id="container"
    class="object-contain max-h-[90vh] max-w-[75vw] z-10 overflow-y-scroll"></div>
</template>
<script setup>
import * as docx from "docx-preview";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useObjectUrl } from "@vueuse/core";

const props = defineProps(["previewEntity"]);
const loading = ref(true);
const blob = ref(null);
const previewURL = useObjectUrl(blob);

async function fetchContent() {
  loading.value = true;
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
    Range: "bytes=0-10000000",
  };
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    {
      method: "GET",
      headers,
    }
  );
  if (res.ok) {
    blob.value = await res.blob();
    docx.renderAsync(
      blob.value,
      document.getElementById("container"),
      document.getElementById("container"),
      {
        ignoreLastRenderedPageBreak: false,
        experimental: true,
      }
    );
    //.then((x) => console.log("docx: finished"));
    loading.value = false;
  }
}

onMounted(() => {
  fetchContent();
});

watch(
  () => props.previewEntity,
  (newValue, oldValue) => {
    fetchContent();
  }
);

onBeforeUnmount(() => {
  loading.value = true;
  blob.value = null;
});
</script>
