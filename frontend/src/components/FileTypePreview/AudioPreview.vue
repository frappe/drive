<template>
  <LoadingIndicator
    v-show="loading"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <audio
    v-show="!loading"
    :key="src"
    ref="mediaRef"
    class="w-1/4 max-h-full"
    autoplay
    preload="none"
    controls="true"
    controlslist="nodownload noremoteplayback noplaybackrate"
    @loadedmetadata="handleMediaReady"
  >
    <source :src="src" :type="type" />
  </audio>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui"
import { ref, onBeforeUnmount, watch, onMounted } from "vue"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
  },
})
const loading = ref(true)
const src = ref(
  `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`
)
const type = ref("audio/mp3")
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

/* watch(() => mediaRef.value, (newValue, oldValue) => {
  console.log(newValue)
  if (newValue) {
    if (newValue.readyState === 1) {
      loading.value = false;
    }
  }
}); */

onMounted(() => {
  loading.value = false
})

onBeforeUnmount(() => {
  loading.value = true
  src.value = ""
  type.value = ""
})
</script>
