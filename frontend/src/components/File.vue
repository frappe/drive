<template>
  <div
    class="h-2/3 flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)] overflow-hidden"
  >
    <img loading="lazy" :class="parsedStyled" :src="link" :draggable="false" />
  </div>
  <div
    class="p-2 max-h-1/3 min-h-1/3 content-center grid border-t border-gray-100"
  >
    <span class="truncate text-base font-medium text-gray-800">
      {{ title }}
    </span>
    <div class="flex items-center justify-start mt-2">
      <p :title="modified" class="truncate text-xs text-gray-600">
        {{ file_size }} ∙ {{ relativeModified }}
      </p>
    </div>
  </div>
</template>
<script>
import { formatMimeType } from "@/utils/format"
import { getIconUrl, thumbnail_getIconUrl } from "@/utils/getIconUrl"

export default {
  name: "File",
  props: {
    file_kind: String,
    mime_type: String,
    file_ext: String,
    name: String,
    title: String,
    relativeModified: String,
    modified: String,
    file_size: String,
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
