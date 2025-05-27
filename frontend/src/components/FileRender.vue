<template>
  <div
    v-if="error"
    class="max-w-[450px] px-16 py-8 z-10 bg-white rounded-md text-neutral-100 text-xl text-center font-medium shadow-xl flex flex-col justify-center items-center"
  >
    <FeatherIcon
      class="h-12 mb-4 fill-blue-500 stroke-white"
      name="alert-circle"
    />
    <span class="mb-4">Cannot open file</span>
    <span class="text-base text-center text-gray-700">
      {{ error }}
    </span>
    <Button class="mt-4 w-full" variant="solid" @click="download">
      Download
    </Button>
  </div>
  <template v-else>
    <component :is="previewComponent" :preview-entity="previewEntity" />
  </template>
</template>
<script setup>
import { FeatherIcon } from "frappe-ui"
import SheetPreview from "@/components/FileTypePreview/SheetPreview.vue"
import ImagePreview from "@/components/FileTypePreview/ImagePreview.vue"
import DocPreview from "@/components/FileTypePreview/DocPreview.vue"
import PDFPreview from "./FileTypePreview/PDFPreview.vue"
import VideoPreview from "./FileTypePreview/VideoPreview.vue"
import TextPreview from "./FileTypePreview/TextPreview.vue"
import AudioPreview from "@/components/FileTypePreview/AudioPreview.vue"
import { computed } from "vue"

const props = defineProps({
  previewEntity: {
    type: Object,
    required: true,
  },
  modelValue: {
    type: Boolean,
    required: false,
    default: true,
  },
})

const error = computed(() => {
  if (props.previewEntity.file_type === "Unknown")
    return "Previews are not supported for this file type. Would you like to download it instead?"
  else if (props.previewEntity.file_size > 10 * 1024 * 1024)
    return "This is too large to preview - would you like to download instead?"
  return false
})

const download = () => {
  window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}&trigger_download=1`
}

const RENDERS = {
  PDF: PDFPreview,
  Image: ImagePreview,
  Video: VideoPreview,
  Audio: AudioPreview,
  // Not Frappe Doc
  Document: DocPreview,
  Spreadsheet: SheetPreview,
  Text: TextPreview,
  Markdown: TextPreview,
}
const previewComponent = computed(() => RENDERS[props.previewEntity.file_type])
</script>
