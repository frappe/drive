<template>
  <div
    class="h-3/5 flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)] overflow-hidden bg-gray-50"
  >
    <img
      loading="lazy"
      :class="
        isThumbnail
          ? 'h-full min-w-full object-cover rounded-t-[calc(theme(borderRadius.lg)-1px)]'
          : 'h-10 w-auto'
      "
      :src="mime_link"
      :draggable="false"
    />
  </div>
  <div class="p-2 h-2/5 content-center grid border-t border-gray-100">
    <span class="truncate text-base font-medium text-gray-800">
      {{ file.title }}
    </span>
    <div class="mt-1 text-xs text-gray-600">
      <div class="flex items-center justify-start gap-1">
        <img
          v-if="formattedType !== 'unknown'"
          loading="lazy"
          class="h-4 w-auto"
          :src="
            getIconUrl(file.is_group ? 'folder' : formattedType.toLowerCase())
          "
          :draggable="false"
        />
        <p class="truncate">
          {{ file.is_group ? childrenSentence + "∙" : "" }}
          {{ formattedType !== "unknown" ? formattedType + "∙" : "" }}
          {{ file.relativeModified }}
        </p>
      </div>
      <p class="mt-1">
        {{ file.file_size_pretty }}
      </p>
    </div>
  </div>
</template>
<script setup>
import { formatMimeType } from "@/utils/format"
import { getIconUrl, thumbnail_getIconUrl } from "@/utils/getIconUrl"
import { onMounted, ref, computed } from "vue"
const props = defineProps({ file: Object })

const formattedType = formatMimeType(props.file.mime_type, false)
const mime_link = ref(
  getIconUrl(props.file.is_group ? "folder" : formattedType.toLowerCase())
)
const isThumbnail = ref(false)
const childrenSentence = computed(() => {
  if (!props.file.children) return "Empty"
  return props.file.children + " item" + (props.file.children === 1 ? "" : "s")
})

onMounted(async () => {
  if (!["Image", "Video"].includes(formattedType)) return
  const result = await thumbnail_getIconUrl(
    formatMimeType(props.file.mime_type),
    props.file.name,
    props.file.file_ext
  )
  if (result.href !== mime_link.value.href) {
    mime_link.value = result
    isThumbnail.value = true
  }
})
</script>
