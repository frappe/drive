<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full z-10 text-neutral-100 mx-auto" />
  <div
    v-else-if="error"
    class="p-8 z-10 bg-gray-900 text-white rounded-md text-neutral-100 text-xl text-center font-medium">
    {{ error }}
  </div>
  <template v-else>
    <VideoPreview v-if="isVideo" :preview-entity="previewEntity" />
    <TextPreview v-if="isTxt" :preview-entity="previewEntity" />
    <SheetPreview v-if="isXlsx" :preview-entity="previewEntity" />
    <ImagePreview v-if="isImage" :preview-entity="previewEntity" />
    <DocPreview v-if="isDocx" :preview-entity="previewEntity" />
    <PDFPreview v-if="isPdf" :preview-entity="previewEntity" />
  </template>
</template>
<script>
import { LoadingIndicator } from "frappe-ui";
import SheetPreview from "@/components/FileTypePreview/SheetPreview.vue";
import ImagePreview from "@/components/FileTypePreview/ImagePreview.vue";
import DocPreview from "@/components/FileTypePreview/DocPreview.vue";
import PDFPreview from "./FileTypePreview/PDFPreview.vue";
import VideoPreview from "./FileTypePreview/VideoPreview.vue";
import TextPreview from "./FileTypePreview/TextPreview.vue";

export default {
  name: "FileRender",
  components: {
    LoadingIndicator,
    SheetPreview,
    ImagePreview,
    DocPreview,
    PDFPreview,
    VideoPreview,
    TextPreview,
  },
  props: {
    previewEntity: {
      type: Object,
      required: true,
    },
  },
  computed: {
    isPdf() {
      return this.previewEntity.mime_type === "application/pdf";
    },
    isImage() {
      return this.previewEntity.mime_type?.startsWith("image/");
    },
    isVideo() {
      return (
        this.previewEntity.mime_type === "video/mp4" ||
        this.previewEntity.mime_type === "video/webm"
      );
    },
    isFrappeDoc() {
      return this.previewEntity.mime_type === "frappe_doc";
    },
    isDocx() {
      return (
        this.previewEntity.mime_type ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      );
    },
    isXlsx() {
      return (
        this.previewEntity.mime_type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      );
    },
    isTxt() {
      return (
        this.previewEntity.mime_type?.startsWith("text/") ||
        this.previewEntity.mime_type === "application/json" ||
        this.previewEntity.mime_type === "application/javascript" ||
        this.previewEntity.mime_type === "text/x-python"
      );
    },
  },
  data() {
    return {
      loading: true,
      error: null,
    };
  },
  mounted() {
    this.renderContent();
  },

  watch: {
    previewEntity: {
      handler(newVal, oldVal) {
        this.loading = true;
        this.renderContent();
      },
    },
  },
  beforeUnmount() {
    this.loading = true;
    this.$store.commit("setEntityInfo", []);
  },
  methods: {
    renderContent() {
      const isSupportedType =
        this.previewEntity.mime_type &&
        [
          "image",
          "video",
          "text",
          "text/x-python",
          "application/json",
          "application/javascript",
          "application/pdf",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          "frappe_doc",
        ].some((type) => this.previewEntity.mime_type.startsWith(type));

      if (!isSupportedType) {
        this.error = "Previews are not supported for this file type";
        this.loading = false;
      } else if (this.previewEntity.size_in_bytes > 1000 * 2048 * 2048) {
        // Size limit = 400
        this.error = "File is too large to preview";
        this.loading = false;
      } else {
        this.loading = false;
        this.error = null;
      }
    },
  },
};
</script>
