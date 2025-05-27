<template>
  <div
    class="h-[65%] flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)] overflow-hidden"
  >
    <img
      v-if="isThumbnail !== 'text'"
      loading="lazy"
      :class="
        isThumbnail
          ? 'h-full min-w-full object-cover rounded-t-[calc(theme(borderRadius.lg)-1px)]'
          : 'h-10 w-auto'
      "
      :src="mime_link"
      :draggable="false"
    />
    <!-- Direct padding doesn't work -->
    <div
      v-else
      class="overflow-hidden text-ellipsis whitespace-nowrap h-full w-[calc(100%-1rem)] object-cover rounded-t-[calc(theme(borderRadius.lg)-1px)] py-2"
    >
      <div
        v-html="mime_link"
        class="prose prose-sm pointer-events-none scale-[.39] ml-0 origin-top-left"
      ></div>
    </div>
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
          v-if="file.file_type !== 'Unknown' && !file.is_group"
          loading="lazy"
          class="h-4 w-auto"
          :src="getIconUrl(file.file_type) || '/drive'"
          :draggable="false"
        />
        <p class="truncate">
          {{ file.is_group ? childrenSentence + "∙" : "" }}
          {{ file.file_type !== "Unknown" ? file.file_type + "∙" : "" }}
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
import { getIconUrl, getThumbnailUrl } from "@/utils/getIconUrl"
import { onMounted, ref, computed } from "vue"
const props = defineProps({ file: Object })

// Add this as first load doesn't have .file_type until cache is cleared
const mime_link = ref(
  getIconUrl(
    props.file.is_group
      ? props.file.share_count > 0
        ? "shared-folder"
        : "folder"
      : props.file.file_type?.toLowerCase?.()
  )
)
const isThumbnail = ref(null)
const childrenSentence = computed(() => {
  if (!props.file.children) return "Empty"
  return props.file.children + " item" + (props.file.children === 1 ? "" : "s")
})

onMounted(async () => {
  if (
    !["Image", "Video", "PDF", "Markdown", "Code", "Text", "Document"].includes(
      props.file.file_type
    )
  )
    return
  const result = await getThumbnailUrl(props.file.name, props.file.file_type)
  if (result.href) return
  if (!result.startsWith("blob")) {
    mime_link.value = result
    isThumbnail.value = "text"
  } else if (result.href !== mime_link.value.href) {
    mime_link.value = result
    isThumbnail.value = "image"
  }
})
</script>
