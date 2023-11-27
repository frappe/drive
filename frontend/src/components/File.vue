<template>
  <div
    class="h-2/3 flex items-center justify-center rounded-t-[calc(theme(borderRadius.lg)-1px)]">
    <img :class="parsedStyled" :src="link" :draggable="false" />
  </div>
  <div class="px-2 pb-1 h-1/3 content-center grid border-t border-gray-100">
    <span class="truncate text-sm text-gray-800 mb-1">
      {{ title }}
    </span>
    <div class="truncate text-xs text-gray-600 flex mt-0 place-items-center">
      <!-- <img :src="getIconUrl(formatMimeType(mime_type))" class="h-3.5 mr-1.5" />
      <p>{{ getFileSubtitle() }}</p> -->
      {{ this.file_size }} ∙ {{ this.modified }}
    </div>
  </div>
</template>
<script>
import { formatMimeType } from "@/utils/format";
import { getIconUrl, thumbnail_getIconUrl } from "@/utils/getIconUrl";

export default {
  name: "File",
  props: {
    mime_type: String,
    file_ext: String,
    name: String,
    title: String,
    modified: String,
    file_size: String,
  },
  setup() {
    return { formatMimeType, getIconUrl, thumbnail_getIconUrl };
  },
  data: function () {
    return {
      link: new URL(
        `/src/assets/images/icons/${this.mime_type}.svg`,
        import.meta.url
      ),
    };
  },
  computed: {
    parsedStyled() {
      if (typeof this.link === "string") {
        return "h-full min-w-full object-cover rounded-t-[calc(theme(borderRadius.lg)-1px)]";
      } else {
        return "h-7 w-7";
      }
    },
  },
  created() {
    this.thumbnailUrl();
  },
  methods: {
    async thumbnailUrl() {
      let result = await thumbnail_getIconUrl(
        formatMimeType(this.mime_type),
        this.name,
        this.file_ext
      );
      this.link = result;
    },
    getFileSubtitle() {
      let fileSubtitle = formatMimeType(this.mime_type);
      fileSubtitle =
        fileSubtitle.charAt(0).toUpperCase() + fileSubtitle.slice(1);
      return `${fileSubtitle} ∙ ${this.modified}`;
    },
  },
};
</script>
