<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10"
  />
  <div
    class="max-w-4/5 max-h-[90%] overflow-auto items-center justify-center flex"
  >
    <img
      v-show="!loading"
      draggable="false"
      class="self-center justify-center"
      :src="previewURL"
    />
  </div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui"
import { onBeforeUnmount, onMounted, ref, watch, inject } from "vue"
import { useObjectUrl } from "@vueuse/core"

const props = defineProps({
  previewEntity: Object,
})

const loading = ref(true)
const imgBlob = ref(null)
const previewURL = useObjectUrl(imgBlob)
const emitter = inject("emitter")

watch(props.previewEntity, () => {
  loading.value = true
  imgBlob.value = null
  fetchContent()
})

async function fetchContent() {
  loading.value = true
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
  }
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    {
      method: "GET",
      headers,
    }
  )
  if (res.ok) {
    imgBlob.value = await res.blob()
    loading.value = false
    console.log("hii")
  }
}

emitter.on("printFile", () => {
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
  }
)

onMounted(() => {
  fetchContent()
})

onBeforeUnmount(() => {
  emitter.off("printFile")
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
  background-size: 30px 30px; /* Must be a square */
  background-position: 0 0, 15px 0, 15px -15px, 0px 15px; /* Must be half of one side of the square */
}
</style>
