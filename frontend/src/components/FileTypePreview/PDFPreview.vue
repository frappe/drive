<template>
  <div v-if="isMobile" class="flex flex-col gap-3 w-96 h-full justify-between grow">
    <div class="flex gap-2 justify-center items-center">
      <Button @click="scale -= 0.25" :disabled="scale <= 0.25" label="-" />
      <span class="text-sm">{{ Math.round(scale * 100) }}%</span>
      <Button @click="scale += 0.25" :disabled="scale >= 2" label="+" />
    </div>
    <div class="grow flex items-center justify-center border rounded-sm max-h-[70vh] overflow-auto">
      <LoadingIndicator v-if="loading" class="w-10 text-ink-gray-8 mx-auto h-full" />
      <canvas ref="canvasRef" :class="{ hidden: loading }" class="rounded-sm" />
    </div>
    <div v-if="totalPages" class="flex gap-2 justify-center items-center">
      <Button label="Prev" :disabled="currentPage <= 1" @click="currentPage--" />
      <span class="text-sm">{{ currentPage }} / {{ totalPages }}</span>
      <Button label="Next" :disabled="currentPage >= totalPages" @click="currentPage++" />
    </div>
  </div>
  <embed
    v-else
    :src
    type="application/pdf"
    class="w-full h-full max-h-[80vh] max-w-[80vw] self-center"
  />
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { LoadingIndicator } from 'frappe-ui'
import { breakpointsTailwind, useBreakpoints } from '@vueuse/core'
import * as PDFJS from 'pdfjs-dist'

PDFJS.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()

const breakpoints = useBreakpoints(breakpointsTailwind)
const isMobile = breakpoints.smaller('sm')

const props = defineProps({ previewEntity: Object })
const src = computed(
  () => `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`
)

const canvasRef = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1)
const loading = ref(true)
let pdfDoc = null

async function loadPDF() {
  loading.value = true
  const task = PDFJS.getDocument(src.value)
  pdfDoc = await task.promise
  totalPages.value = pdfDoc.numPages
  await renderPage(currentPage.value)
  loading.value = false
}

async function renderPage(num) {
  if (!pdfDoc || !canvasRef.value) return
  const page = await pdfDoc.getPage(num)
  const viewport = page.getViewport({ scale: scale.value })
  const canvas = canvasRef.value
  canvas.height = viewport.height
  canvas.width = viewport.width
  await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
}

watch(currentPage, (num) => renderPage(num))
watch(scale, () => renderPage(currentPage.value))

onMounted(() => {
  if (isMobile.value) loadPDF()
})
</script>
