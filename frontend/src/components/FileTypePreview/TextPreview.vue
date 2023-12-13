<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full z-10 text-neutral-100 mx-auto" />
  <div
    v-else
    id="container"
    class="w-full h-full overflow-auto p-4 text-base border">
    <pre
      class="p-3 font-mono f-full h-full bg-white overflow-x-scroll overflow-y-scroll"
      >{{ blob }}</pre
    >
  </div>
</template>

<script setup>
/* Consider adding https://codemirror.net/ and add a mimetype eval list for all possible mimetypes */

import { LoadingIndicator } from "frappe-ui";
import { onMounted, ref, watch } from "vue";

const props = defineProps(["previewEntity"]);
const loading = ref(true);
const blob = ref(null);

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
    let resBlob = await res.blob();
    blob.value = await resBlob.text();
    loading.value = false;
  }
}
watch(
  () => props.previewEntity,
  (newValue, oldValue) => {
    fetchContent();
  }
);
onMounted(() => {
  fetchContent();
});
</script>
<style scoped></style>
