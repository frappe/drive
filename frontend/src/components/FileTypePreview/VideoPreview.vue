<template>
  <LoadingIndicator
    v-show="loading"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <video
    v-show="!loading"
    :key="src"
    ref="mediaRef"
    class="w-auto max-h-full"
    autoplay
    muted
    preload="none"
    controlslist="nodownload noremoteplayback noplaybackrate disablepictureinpicture"
    controls
    draggable="false"
    @loadedmetadata="handleMediaReady"
  >
    <source :src="src" :type="type" />
  </video>
</template>

<script setup>
/* 
  Add codec evaluation currently assumes its a valid H264/5 (MP4/Webm)
  Look into the feasibility of client side mp4 moov fragmentation pre processing using
  https://github.com/gpac/gpac/wiki/MP4Box
  Server side byte is good enough for now 
*/

import { LoadingIndicator } from "frappe-ui"
import { ref, onBeforeUnmount, watch } from "vue"

const props = defineProps({
  previewEntity: {
    type: String,
    default: "",
  },
})
const loading = ref(true)
const src = ref(
  `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`
)
const type = ref(
  props.previewEntity.mime_type === "video/quicktime"
    ? "video/mp4"
    : props.previewEntity.mime_type
)
const mediaRef = ref("")

const handleMediaReady = (event) => {
  mediaRef.value = event.target
  if (mediaRef.value.readyState === 1) {
    loading.value = false
  }
}

watch(
  () => props.previewEntity,
  (newValue) => {
    loading.value = true
    src.value = `/api/method/drive.api.files.get_file_content?entity_name=${newValue.name}`
    type.value = newValue.mime_type
  }
)

onBeforeUnmount(() => {
  loading.value = true
  src.value = ""
  type.value = ""
})
</script>
