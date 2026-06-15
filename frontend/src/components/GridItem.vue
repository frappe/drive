<template>
  <div
    class="h-[65%] flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)] overflow-hidden"
  >
    <img
      v-show="!imgLoaded"
      loading="lazy"
      class="h-10 w-auto"
      :src="fallback"
      :draggable="false"
    />
    <img
      v-show="imgLoaded"
      :class="
        hasThumbnail
          ? 'h-full min-w-full object-cover rounded-t-[calc(theme(borderRadius.lg)-1px)]'
          : 'h-10 w-auto'
      "
      :src="src"
      :draggable="false"
      @load="imgLoaded = true"
    />
  </div>
  <div
    class="p-2 h-[35%] border-t border-outline-gray-1 flex flex-col justify-evenly"
  >
    <div class="truncate w-full w-fit text-base font-medium text-ink-gray-8">
      {{ file.file_name }}
    </div>
    <div class="mt-[5px] text-xs text-ink-gray-5">
      <div class="flex items-center justify-start gap-1">
        <img
          v-if="showTypeIcon"
          loading="lazy"
          class="h-4 w-auto"
          :src="getIconUrl(file.file_type)"
          :draggable="false"
        />
        <p class="truncate">
          {{ file.is_folder ? childrenSentence + '∙' : '' }}
          {{ file.file_type !== 'Unknown' ? file.file_type + '∙' : '' }}
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
import { getIconUrl, getThumbnailUrl } from '@/utils/files'
import { ref, computed } from 'vue'
const props = defineProps({ file: Object })

const { src, fallback } = getThumbnailUrl(props.file, 'grid')
const hasThumbnail = src !== fallback
const imgLoaded = ref(false)

const showTypeIcon = computed(
  () => hasThumbnail && imgLoaded.value && !props.file.is_folder && props.file.file_type !== 'Unknown'
)

const childrenSentence = computed(() => {
  if (!props.file.child_count) return 'empty'
  return props.file.child_count + ' item' + (props.file.child_count === 1 ? '' : 's')
})
</script>
