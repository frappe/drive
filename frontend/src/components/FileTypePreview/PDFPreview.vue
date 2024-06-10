<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full text-neutral-100 mx-auto"
  />
  <div v-else class="flex flex-col items-start justify-start text-base">
    <!-- Toolbar -->
    <div
      v-if="pages > 100"
      class="flex w-full items-center justify-center rounded-t bg-gray-50 bg-opacity-50 mt-8 border gap-x-2 p-1"
    >
      <Button variant="ghost" icon="chevron-left">Prev</Button>
      <Input
        v-model.number="currentPage"
        type="number"
        class="min-8 w-auto max-w-15 text-center"
        min="1"
        max="pages"
      />
      <span> / {{ pages }}</span>
      <Button
        variant="ghost"
        icon="chevron-right"
        @click="
          currentPage = currentPage < pages ? currentPage + 1 : currentPage
        "
      ></Button>
    </div>

    <div
      class="bg-gray-400 overflow-auto max-h-[85vh] max-w-[65vw] min-w-[55vw] p-2 border"
      :class="pages > 100 ? 'rounded-b' : 'rounded'"
    >
      <div v-if="pages > 100" class="m-4">
        <!-- Paginate -->
        <VuePDF
          id="pdf"
          :pdf="pdf"
          :page="currentPage"
          :text-layer="true"
          :fit-parent="true"
        />
      </div>
      <!-- Scroll -->
      <div v-for="page in pages" v-else :key="page" class="m-4">
        <VuePDF
          id="pdf"
          :pdf="pdf"
          :page="page"
          :text-layer="true"
          :fit-parent="true"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { LoadingIndicator } from "frappe-ui"
import { onMounted, onUnmounted, ref, watch } from "vue"
import { useObjectUrl } from "@vueuse/core"
import { Button, Input } from "frappe-ui"
import { VuePDF, usePDF } from "@tato30/vue-pdf"
import "@tato30/vue-pdf/style.css"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
  },
})
const loading = ref(true)
const blob = ref(null)
const previewURL = useObjectUrl(blob)
const currentPage = ref(1)
const { pdf, pages } = usePDF(previewURL)

async function fetchContent() {
  loading.value = true
  const headers = {
    Accept: "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "X-Frappe-Site-Name": window.location.hostname,
    Range: "bytes=0-10000000",
  }
  const res = await fetch(
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`,
    {
      method: "GET",
      headers,
    }
  )
  if (res.ok) {
    blob.value = await res.blob()
    loading.value = false
  }
}

watch(
  () => props.previewEntity,
  () => {
    fetchContent()
  }
)

onMounted(() => {
  fetchContent()
})
onUnmounted(() => {
  pdf.value?.destroy()
})
</script>
<style>
#pdf {
  user-select: text;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Firefox */
input[type="number"] {
  appearance: inherit;
  -moz-appearance: textfield;
}
</style>
