<template>
  <div v-if="foldersBefore && is_group">
    <div class="flex items-start">
      <svg
        class="h-7.5 w-auto"
        :draggable="false"
        :style="{ fill: color }"
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
            <rect width="16" height="16" fill="white" />
          </clipPath>
        </defs>
      </svg>
    </div>
    <div class="content-center grid mt-2 sm:mt-3.5">
      <span class="truncate text-base font-medium text-gray-800">
        {{ title }}
      </span>
      <p :title="modified" class="truncate text-sm text-gray-600 mt-2">
        {{ file_size ? file_size + " ∙ " : "" }}
        {{ relativeModified }}
      </p>
    </div>
  </div>
  <template v-else>
    <div
      class="h-2/3 flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)] overflow-hidden"
    >
      <!-- Folder Icon -->
      <svg
        v-if="is_group"
        class="h-8.5 w-auto"
        :draggable="false"
        :style="{ fill: color }"
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
            <rect width="16" height="16" fill="white" />
          </clipPath>
        </defs>
      </svg>
      <img
        v-else
        loading="lazy"
        :class="parsedStyled"
        :src="link"
        :draggable="false"
      />
    </div>
    <div class="p-2 h-1/3 content-center grid border-t border-gray-100">
      <span class="truncate text-base font-medium text-gray-800">
        {{ title }}
      </span>
      <div class="flex items-center justify-start mt-2">
        <p :title="modified" class="truncate text-xs text-gray-600">
          {{ file_size }} {{ file_size ? "∙" : null }} {{ relativeModified }}
        </p>
      </div>
    </div>
  </template>
</template>
<script>
import { formatMimeType } from "@/utils/format"
import { getIconUrl, thumbnail_getIconUrl } from "@/utils/getIconUrl"

export default {
  name: "GridItem",
  props: {
    file_kind: String,
    mime_type: String,
    file_ext: String,
    name: String,
    title: String,
    relativeModified: String,
    modified: String,
    file_size: String,
    is_group: Number,
    color: String,
  },
  setup() {
    return { formatMimeType, getIconUrl, thumbnail_getIconUrl }
  },
  data: function () {
    return {
      link: new URL(
        `/src/assets/images/icons/${this.mime_type}.svg`,
        import.meta.url
      ),
    }
  },
  computed: {
    foldersBefore() {
      return this.$store.state.foldersBefore
    },
    parsedStyled() {
      if (typeof this.link === "string") {
        return "h-full min-w-full object-cover rounded-t-[calc(theme(borderRadius.lg)-1px)]"
      } else {
        return "h-10 w-auto"
      }
    },
  },
  created() {
    this.thumbnailUrl()
  },
  methods: {
    async thumbnailUrl() {
      let result = await thumbnail_getIconUrl(
        formatMimeType(this.mime_type),
        this.name,
        this.file_ext
      )
      this.link = result
    },
  },
}
</script>
