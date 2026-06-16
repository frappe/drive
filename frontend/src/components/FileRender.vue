<template>
  <div
    v-if="error"
    class="max-w-[450px] h-fit self-center p-10 border border-outline-gray-2 bg-surface-white rounded-md text-xl text-center font-medium shadow-xl flex flex-col justify-center items-center gap-4"
  >
    <LucideAlertCircle class="size-8 text-ink-gray-8" />
    <span class="text-ink-gray-9">Cannot open file</span>
    <span class="text-base text-center text-ink-gray-7">
      {{ error }}
    </span>
    <Button class="w-full" variant="solid" @click="download"> Download </Button>
  </div>
  <component :is="previewComponent" v-else :preview-entity="previewEntity" />
</template>
<script setup>
import { computed, defineAsyncComponent } from 'vue'

const MSOfficePreview = defineAsyncComponent(() => import('@/components/FileTypePreview/MSOfficePreview.vue'))
const ImagePreview = defineAsyncComponent(() => import('@/components/FileTypePreview/ImagePreview.vue'))
const PDFPreview = defineAsyncComponent(() => import('./FileTypePreview/PDFPreview.vue'))
const VideoPreview = defineAsyncComponent(() => import('./FileTypePreview/VideoPreview.vue'))
const TextPreview = defineAsyncComponent(() => import('./FileTypePreview/TextPreview.vue'))
const AudioPreview = defineAsyncComponent(() => import('@/components/FileTypePreview/AudioPreview.vue'))
import LucideAlertCircle from '~icons/lucide/alert-circle'
import { diskSettings } from '@/resources/permissions'
import store from '@/store'

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

if (!diskSettings.data) diskSettings.fetch()
const error = computed(() => {
  const limit = diskSettings.data?.preview_size || 100
  if (!Object.keys(RENDERS).includes(props.previewEntity.file_type))
    return 'Previews are not supported for this file type. Would you like to download it instead?'
  else if (props.previewEntity.file_size > limit * 1024 * 1024)
    return 'This is too large to preview - would you like to download instead?'
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
}

const EXCEPTIONS = {
  'text/csv': 'Text',
}

const getType = (k) => {
  return EXCEPTIONS[k.mime_type] || k.file_type
}
const previewComponent = computed(() => RENDERS[getType(props.previewEntity)])
</script>
