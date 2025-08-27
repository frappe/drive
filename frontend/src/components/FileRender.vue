<template>
  <div
    v-if="error"
    class="max-w-[450px] px-16 py-8 z-10 bg-surface-white rounded-md text-neutral-100 text-xl text-center font-medium shadow-xl flex flex-col justify-center items-center"
  >
    <LucideAlertCircle class="h-12 mb-4 fill-blue-500 stroke-white" />
    <span class="mb-4">{{ __("Cannot open file") }}</span>
    <span class="text-base text-center text-ink-gray-7">
      {{ error }}
    </span>
    <Button
      class="mt-4 w-full"
      variant="solid"
      @click="download"
    >
      Tải xuống
    </Button>
  </div>
  <template v-else>
    <component
      :is="previewComponent"
      :preview-entity="previewEntity"
    />
  </template>
</template>
<script setup>
import AudioPreview from "@/components/FileTypePreview/AudioPreview.vue"
import ImagePreview from "@/components/FileTypePreview/ImagePreview.vue"
import MSOfficePreview from "@/components/FileTypePreview/MSOfficePreview.vue"
import { computed } from "vue"
import LucideAlertCircle from "~icons/lucide/alert-circle"
import PDFPreview from "./FileTypePreview/PDFPreview.vue"
import TextPreview from "./FileTypePreview/TextPreview.vue"
import VideoPreview from "./FileTypePreview/VideoPreview.vue"

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
  if (!Object.keys(RENDERS).includes(props.previewEntity.file_type))
    return "Làm ơn tải xuống để xem tệp này. Hỗ trợ xem trước cho các loại tệp khác đang được phát triển."
  else if (props.previewEntity.file_size > 100 * 1024 * 1024)
    return "Tệp này quá lớn để xem trước - bạn có muốn tải xuống không?"
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
  Document: MSOfficePreview,
  Spreadsheet: MSOfficePreview,
  Presentation: MSOfficePreview,
  Text: TextPreview,
  Code: TextPreview,
  Markdown: TextPreview,
}
const previewComponent = computed(() => RENDERS[props.previewEntity.file_type])
</script>
