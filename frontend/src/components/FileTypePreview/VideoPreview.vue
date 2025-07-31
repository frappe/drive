<template>
  <div class="flex justify-center items-center w-full h-full bg-black p-2">
    <LoadingIndicator v-show="loading" class="w-10" />

    <video
      v-show="!loading"
      :key="src"
      ref="mediaRef"
      class="max-w-full max-h-[70vh] object-contain self-center rounded-lg shadow"
      autoplay
      muted
      preload="none"
      controls
      controlslist="nodownload noremoteplayback noplaybackrate disablepictureinpicture"
      draggable="false"
      @loadedmetadata="handleMediaReady"
    >
      <source :src="src" :type="type" />
    </video>
  </div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui"
import { ref, onBeforeUnmount, watch } from "vue"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: () => ({}),
  },
})

const loading = ref(true)
const src = ref("")
const type = ref("")
const mediaRef = ref(null)

const setSource = (entity) => {
  if (!entity?.name) return
  loading.value = true
  src.value = `/api/method/drive.api.files.get_file_content?entity_name=${entity.name}`
  type.value =
    entity.mime_type === "video/quicktime" ? "video/mp4" : entity.mime_type
}

const handleMediaReady = (event) => {
  mediaRef.value = event.target
  if (mediaRef.value.readyState >= 1) {
    loading.value = false
  }
}

// Initial load
setSource(props.previewEntity)

// Watch for changes
watch(
  () => props.previewEntity,
  (newValue) => {
    setSource(newValue)
  }
)

onBeforeUnmount(() => {
  loading.value = true
  src.value = ""
  type.value = ""
})
</script>

<style scoped>
video::-internal-media-controls-download-button {
  display: none;
}
</style>
