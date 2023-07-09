<template>
  <div class="h-32 place-items-center grid">
    <img
      :src="link"
      class="h-32 w-full object-cover object-contain"
      :draggable="false" />
  </div>
  <div class="px-3.5 h-16 content-center grid">
    <h3 class="truncate text-[14px] font-medium">{{ this.title }}</h3>
    <div class="truncate text-sm text-gray-600 flex mt-1 place-items-center">
      <img
        :src="getIconUrl(formatMimeType(this.mime_type))"
        class="h-3.5 mr-1.5" />
      <p>{{ getFileSubtitle() }}</p>
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
    name: String,
    title: String,
    modified: String,
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
  created() {
    this.thumbnailUrl();
  },
  methods: {
    async thumbnailUrl() {
      let result = await thumbnail_getIconUrl(
        formatMimeType(this.mime_type),
        this.name
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
