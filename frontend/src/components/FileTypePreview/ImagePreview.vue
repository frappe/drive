<template>
  <div class="relative">
    <!-- Thumbnail preview -->
    <img
      :src="previewURL"
      class="max-w-full max-h-[80vh] cursor-zoom-in object-contain mx-auto"
      @click="openFullPreview"
    />

    <!-- Fullscreen preview -->
    <div
      v-if="showFull"
      class="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center"
      @click.self="closeFullPreview"
    >
      <img
        :src="previewURL"
        class="max-w-full max-h-full object-contain"
        :style="{ imageRendering: 'auto' }"
      />
      <button
        class="absolute top-4 right-4 text-white text-3xl font-bold"
        @click="closeFullPreview"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue"
import { useObjectUrl } from "@vueuse/core"

const props = defineProps({
  previewEntity: Object,
})

const imgBlob = ref(null)
const previewURL = useObjectUrl(imgBlob)
const showFull = ref(false)

watch(
  () => props.previewEntity,
  () => fetchContent(),
  { immediate: true }
)

async function fetchContent() {
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    { method: "GET" }
  )
  if (res.ok) {
    imgBlob.value = await res.blob()
  }
}

function openFullPreview() {
  showFull.value = true
  document.body.style.overflow = "hidden" // Disable background scroll
}

function closeFullPreview() {
  showFull.value = false
  document.body.style.overflow = "" // Re-enable scroll
}
</script>

<style scoped>
img {
  background-image: linear-gradient(45deg, #ccc 25%, transparent 25%),
    linear-gradient(135deg, #ccc 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #ccc 75%),
    linear-gradient(135deg, white 75%, #ccc 75%);
  background-size: 30px 30px;
  background-position: 0 0, 15px 0, 15px -15px, 0px 15px;
}
</style>
