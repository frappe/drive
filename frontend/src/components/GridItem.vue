<template>
  <div
    class="h-[65%] flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)] overflow-hidden"
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
  <div
    class="p-2 h-[35%] border-t border-gray-100 flex flex-col justify-evenly"
  >
    <div class="truncate w-full w-fit text-base font-medium text-gray-800">
      {{ file.title }}
    </div>
    <div class="mt-[5px] text-xs text-gray-600">
      <div class="flex items-center justify-start gap-1">
        <img
          v-if="formattedType !== 'Unknown' && !file.is_group"
          loading="lazy"
          class="h-4 w-auto"
          :src="getIconUrl(formattedType.toLowerCase()) || '/drive'"
          :draggable="false"
        />
        <p class="truncate">
          {{ file.is_group ? childrenSentence + "∙" : "" }}
          {{ formattedType !== "Unknown" ? formattedType + "∙" : "" }}
          {{ file.relativeModified }}
        </p>
      </div>
      <!-- <p class="mt-1">
        {{ file.file_size_pretty }}
      </p> -->
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
  getIconUrl(
    props.file.is_group
      ? props.file.share_count > 0
        ? "shared-folder"
        : "folder"
      : formattedType.toLowerCase()
  )
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
