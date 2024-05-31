<template>
  <LoadingIndicator
    v-if="loading"
    class="w-10 h-full z-10 text-neutral-100 mx-auto"
  />
  <div
    v-else-if="error"
    class="max-w-[450px] px-16 py-8 z-10 bg-white rounded-md text-neutral-100 text-xl text-center font-medium shadow-xl flex flex-col justify-center items-center"
  >
    <FeatherIcon
      class="h-12 mb-4 fill-blue-500 stroke-white"
      name="alert-circle"
    />
    <span class="mb-4">Cannot open file</span>
    <span class="text-base text-center text-gray-700">
      {{ error }}
    </span>
    <Button
      v-if="
        $store.state.entityInfo[0].allow_download ||
        $store.state.entityInfo[0].owner === 'You'
      "
      class="mt-4 w-full"
      variant="solid"
      @click="download"
    >
      Download
    </Button>
  </div>
  <template v-else>
    <VideoPreview v-if="isVideo" :preview-entity="previewEntity" />
    <AudioPreview v-if="isAudio" :preview-entity="previewEntity" />
    <TextPreview v-if="isTxt" :preview-entity="previewEntity" />
    <SheetPreview v-if="isXlsx" :preview-entity="previewEntity" />
    <ImagePreview v-if="isImage" :preview-entity="previewEntity" />
    <DocPreview v-if="isDocx" :preview-entity="previewEntity" />
    <PDFPreview v-if="isPdf" :preview-entity="previewEntity" />
  </template>
</template>
<script>
import { LoadingIndicator, FeatherIcon } from "frappe-ui"
import SheetPreview from "@/components/FileTypePreview/SheetPreview.vue"
import ImagePreview from "@/components/FileTypePreview/ImagePreview.vue"
import DocPreview from "@/components/FileTypePreview/DocPreview.vue"
import PDFPreview from "./FileTypePreview/PDFPreview.vue"
import VideoPreview from "./FileTypePreview/VideoPreview.vue"
import TextPreview from "./FileTypePreview/TextPreview.vue"
import AudioPreview from "@/components/FileTypePreview/AudioPreview.vue"

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
    AudioPreview,
    FeatherIcon,
  },
  props: {
    previewEntity: {
      type: Object,
      required: true,
    },
    modelValue: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  emits: ["update:modelValue"],
  data() {
    return {
      loading: true,
      error: null,
    }
  },
  computed: {
    isPdf() {
      return this.previewEntity.mime_type === "application/pdf"
    },
    isImage() {
      return this.previewEntity.mime_type?.startsWith("image/")
    },
    isAudio() {
      return this.previewEntity.mime_type?.startsWith("audio/")
    },
    isVideo() {
      return (
        this.previewEntity.mime_type === "video/mp4" ||
        this.previewEntity.mime_type === "video/webm" ||
        this.previewEntity.mime_type === "video/quicktime"
      )
    },
    isFrappeDoc() {
      return this.previewEntity.mime_type === "frappe_doc"
    },
    isDocx() {
      return (
        this.previewEntity.mime_type ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      )
    },
    isXlsx() {
      return (
        this.previewEntity.mime_type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      )
    },
    isTxt() {
      return (
        this.previewEntity.mime_type?.startsWith("text/") ||
        this.previewEntity.mime_type === "application/json" ||
        this.previewEntity.mime_type === "application/javascript" ||
        this.previewEntity.mime_type === "text/x-python"
      )
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
        if (!value) {
          this.folderName = ""
          this.errorMessage = ""
        }
      },
    },
  },

  watch: {
    previewEntity: {
      handler() {
        this.loading = true
        this.renderContent()
      },
    },
  },
  mounted() {
    this.renderContent()
  },
  beforeUnmount() {
    this.loading = true
    this.$store.commit("setEntityInfo", [])
  },
  methods: {
    renderContent() {
      const isSupportedType =
        this.previewEntity.mime_type &&
        [
          "image",
          "video/quicktime",
          "video/webm",
          "video/mp4",
          "audio",
          "text",
          "text/x-python",
          "application/json",
          "application/javascript",
          "application/pdf",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          "frappe_doc",
        ].some((type) => this.previewEntity.mime_type.startsWith(type))

      if (!isSupportedType) {
        this.error = "Previews are not supported for this file type"
        if (
          this.$store.state.entityInfo[0].allow_download ||
          this.$store.state.entityInfo[0].owner === "You"
        ) {
          this.error =
            "Previews are not supported for this file type. Would you like to download it instead?"
        }
        this.loading = false
      } else if (
        this.previewEntity.mime_type.startsWith("video") &&
        this.previewEntity.size_in_bytes < 2000 * 1024 * 1024
      ) {
        this.loading = false
      } else if (this.previewEntity.size_in_bytes > 400 * 1024 * 1024) {
        this.error = "File is too large to preview"
        this.loading = false
      } else {
        this.loading = false
        this.error = null
      }
    },
    download() {
      window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}&trigger_download=1`
    },
  },
}
</script>
