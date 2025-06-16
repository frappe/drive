<template>
  <div
    :title="title ? title : entity.title"
    class="border max-w-[220px] rounded-[7px] px-1 py-1 flex items-center justify-center gap-x-1 overflow-clip"
  >
    <svg
      v-if="!strikeThrough && entity.is_group"
      class="h-3.5 mr-0.5"
      :draggable="false"
      :style="{ fill: entity.color }"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clip-path="url(#clip0_1942_59507)">
        <path
          d="M7.83412 2.88462H1.5C1.22386 2.88462 1 3.10847 1 3.38462V12.5C1 13.6046 1.89543 14.5 3 14.5H13C14.1046 14.5 15 13.6046 15 12.5V2C15 1.72386 14.7761 1.5 14.5 1.5H9.94008C9.88623 1.5 9.83382 1.51739 9.79065 1.54957L8.13298 2.78547C8.04664 2.84984 7.94182 2.88462 7.83412 2.88462Z"
        />
      </g>
      <defs>
        <clipPath id="clip0_1942_59507">
          <rect
            width="16"
            height="16"
            fill="white"
          />
        </clipPath>
      </defs>
    </svg>
    <img
      v-else-if="!strikeThrough"
      loading="lazy"
      class="h-full"
      :src="getIconUrl(entity.file_type)"
      :draggable="false"
    />
    <span
      class="text-sm line-clamp-1 text-ink-gray-6"
      :class="strikeThrough ? 'line-through ' : ' '"
      >{{ title ? title : entity.title }}</span
    >
  </div>
</template>
<script setup>
import { getIconUrl } from "../utils/getIconUrl"

defineProps({
  title: {
    type: String,
    default: "File",
    required: false,
  },
  activity: {
    type: Object,
    required: true,
  },
  entity: {
    type: Object,
    required: true,
  },
  strikeThrough: {
    type: Boolean,
    default: false,
    required: false,
  },
})
</script>
