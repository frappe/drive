<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full text-neutral-100 mx-auto" />
  <video
    v-else
    class="w-auto max-h-full"
    autoplay
    preload="none"
    controlslist="nodownload noremoteplayback noplaybackrate disablepictureinpicture"
    controls
    type="video/mp4"
    :src="previewURL"></video>
</template>

<script setup>
/* Add codec evaluation currently assumes its a valid H265/4 (MP4/Webm)*/

import { LoadingIndicator } from "frappe-ui";
import { onMounted, ref, watch } from "vue";
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
