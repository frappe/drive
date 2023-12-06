<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full z-10 text-neutral-100 mx-auto" />
  <img class="w-full h-auto" v-else :src="previewURL" />
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useObjectUrl } from "@vueuse/core";

const props = defineProps(["previewEntity"]);
const loading = ref(true);
const imgBlob = ref(null);
const previewURL = useObjectUrl(imgBlob);

watch(props.previewEntity, (newVal, oldVal) => {
  loading.value = false;
  imgBlob.value = null;
  console.log("Prop Changed!", newValue);
  fetchContent();
});

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
    loading.value = false;
    imgBlob.value = await res.blob();
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

onBeforeUnmount(() => {
  loading.value = true;
  imgBlob.value = null;
});
</script>
