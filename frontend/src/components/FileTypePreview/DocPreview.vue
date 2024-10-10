<template>
  <div
    id="DocxContainer"
    class="object-contain h-[85vh] max-w-[65vw] z-10 overflow-y-auto rounded border"
  ></div>
</template>
<script setup>
import * as docx from "docx-preview"
import { onBeforeUnmount, onMounted, ref, watch, inject } from "vue"

const props = defineProps({
  previewEntity: {
    type: Object,
    default: null,
  },
})

const loading = ref(true)
const blob = ref(null)
const emitter = inject("emitter")

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
    blob.value = await res.blob()
    docx.renderAsync(
      blob.value,
      document.getElementById("DocxContainer"),
      document.getElementById("DocxContainer"),
      {
        ignoreLastRenderedPageBreak: false,
        experimental: true,
      }
    )
    //.then((x) => console.log("docx: finished"));
    loading.value = false
  }
}

function stripStyles(element) {
  const clone = element.cloneNode(true)
  const allElements = clone.getElementsByTagName("*")
  for (const el of allElements) {
    el.removeAttribute("style")
  }
  return clone
}

emitter.on("printFile", () => {
  const printFrame = document.createElement("iframe")
  document.body.appendChild(printFrame)
  const docxContainer = document.getElementById("DocxContainer")
  console.log(docxContainer)
  const content = docxContainer ? docxContainer.innerHTML : ""
  printFrame.contentWindow.document.open()
  printFrame.contentWindow.document.write(`
    <html>
    <style>
        @media print {
        .docx-wrapper {
          box-shadow: none !important;
          background: none !important;
          padding: 0px !important;
          padding-bottom: 0px !important;
        }
        .docx-wrapper>section.docx {
          background: white !important;
          box-shadow: none !important;
          margin-bottom: 0px !important;
          }
        }
      </style>
      <body>
        ${content}
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

onMounted(() => {
  fetchContent()
})

watch(
  () => props.previewEntity,
  () => {
    fetchContent()
  }
)

onBeforeUnmount(() => {
  emitter.off("printFile")
  loading.value = true
  blob.value = null
})
</script>

<style>
#DocxContainer {
  user-select: text;
}
</style>
