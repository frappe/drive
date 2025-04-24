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
import { onBeforeMount, computed } from "vue"
import { useStore } from "vuex"

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
const store = useStore()

const SUPPORTED_TYPES = [
  "image",
  "video/quicktime",
  "video/webm",
  "video/mp4",
  "audio",
  "text",
  "text/x-python",
  "application/json",
  "application/javascript",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "frappe_doc",
]
const error = computed(() => {
  const isSupportedType =
    props.previewEntity.mime_type &&
    SUPPORTED_TYPES.some((type) =>
      props.previewEntity.mime_type.startsWith(type)
    )
  if (!isSupportedType)
    return "Previews are not supported for this file type. Would you like to download it instead?"
  else if (props.previewEntity.file_size > 400 * 1024 * 1024)
    return "This is too large to preview - would you like to download instead?"
  return false
})

const download = () => {
  window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}&trigger_download=1`
}

const previewComponent = computed(() => {
  return {
    [props.previewEntity.mime_type === "application/pdf"]: PDFPreview,
    [props.previewEntity.mime_type === "video/mp4" ||
    props.previewEntity.mime_type === "video/webm" ||
    props.previewEntity.mime_type === "video/quicktime"]: VideoPreview,
    [props.previewEntity.mime_type?.startsWith("image/")]: ImagePreview,
    [props.previewEntity.mime_type?.startsWith("audio/")]: AudioPreview,
    [props.previewEntity.mime_type ===
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
      DocPreview,

    [props.previewEntity.mime_type ===
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
      SheetPreview,
    [props.previewEntity.mime_type?.startsWith("text/") ||
    props.previewEntity.mime_type === "application/json" ||
    props.previewEntity.mime_type === "application/javascript" ||
    props.previewEntity.mime_type === "text/x-python"]: TextPreview,
  }[true]
})
</script>
