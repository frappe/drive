<template>
  <LoadingIndicator
    v-show="loading"
    class="w-10"
  />

  <template v-if="!loading && previewURL">
    <img
      draggable="false"
      class="w-4/5 h-fit self-center"
      :src="previewURL"
      alt="Preview Image"
    />
  </template>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, inject } from "vue"
import { useObjectUrl } from "@vueuse/core"
import { LoadingIndicator } from "frappe-ui"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
  },
})

const loading = ref(true)
const imgBlob = ref(null)
const previewURL = useObjectUrl(imgBlob)
const emitter = inject("emitter")

async function fetchContent() {
  if (!props.previewEntity?.name) return

  loading.value = true
  imgBlob.value = null

  try {
    const res = await fetch(
      `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
      {
        method: "GET",
        headers: {
          "X-Frappe-Site-Name": window.location.hostname,
        },
      }
    )

    if (!res.ok) throw new Error("Failed to fetch image")

    const blob = await res.blob()

    if (!blob.type.startsWith("image/")) {
      throw new Error("Not an image file")
    }

    imgBlob.value = blob
  } catch (err) {
    console.error("Error loading image:", err)
  } finally {
    loading.value = false
  }
}

emitter?.on("printFile", () => {
  const printFrame = document.createElement("iframe")
  printFrame.style.position = "absolute"
  printFrame.style.width = "0"
  printFrame.style.height = "0"
  printFrame.style.border = "none"
  document.body.appendChild(printFrame)
  printFrame.contentWindow.document.open()
  printFrame.contentWindow.document.write(`
    <html>
      <head>
        <style>
          img {
            max-width: 100%;
            height: auto;
          }
        </style>
      </head>
      <body>
        <img src="${previewURL.value}" />
      </body>
    </html>
  `)
  printFrame.contentWindow.document.close()
  printFrame.contentWindow.focus()
  printFrame.contentWindow.print()
  printFrame.onload = () => {
    setTimeout(() => {
      document.body.removeChild(printFrame)
    }, 100)
  }
})

watch(
  () => props.previewEntity,
  () => {
    fetchContent()
  },
  { immediate: true }
)

onMounted(fetchContent)

onBeforeUnmount(() => {
  emitter?.off("printFile")
  loading.value = true
  imgBlob.value = null
})
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
