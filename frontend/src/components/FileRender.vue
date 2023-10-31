<template>
  <LoadingIndicator
    v-if="preview.loading"
    class="w-10 h-10 z-10 text-neutral-100 mx-auto" />
  <div
    v-else-if="preview.error"
    class="p-8 z-10 bg-gray-900 text-white rounded-md text-neutral-100 text-xl text-center font-medium">
    {{ preview.error }}
  </div>

  <!--     <video-player
      class="video-js vjs-fluid"
      type="video/mp4"
      v-if="
        isVideo &&
        videoOptions.sources[0].src &&
        !this.preview.error &&
        !this.preview.loading
      "
      :options="videoOptions" /> -->
  <video
    v-if="
      isVideo &&
      videoOptions.sources[0].src &&
      !preview.error &&
      !preview.loading
    "
    controls
    type="video/mp4"
    :src="videoOptions.sources[0].src"></video>
  <img v-if="isImage" :src="preview.url" class="object-contain max-h-[85vh]" />
  <div
    v-if="isTxt"
    id="container"
    class="w-full h-full overflow-auto p-4 text-base border">
    <pre
      class="p-3 font-mono f-full h-full bg-white overflow-x-scroll overflow-y-scroll"
      >{{ textFileContent }}</pre
    >
  </div>
  <div
    v-if="isDocx"
    id="container"
    class="object-contain max-h-[95vh] max-w-[75vw] z-10 overflow-y-scroll"></div>
  <div
    v-if="isXlsx"
    id="ctr"
    class="object-contain max-h-[95vh] max-w-[80vw] z-10 overflow-y-scroll">
    <div v-once id="gridctr"></div>
  </div>
  <div
    v-if="isPdf"
    class="max-h-[95vh] max-w-[75vw] z-10 bg-[#252728] rounded-lg shadow-xl">
    <iframe class="w-full min-w-[75vw] h-[90vh]" :src="preview.url" />
  </div>
</template>
<script>
import { LoadingIndicator } from "frappe-ui";
/* import VideoPlayer from "@/components/VideoPlayer.vue";
 */ import * as docx from "docx-preview";
import { read, utils } from "xlsx";
import canvasDatagrid from "canvas-datagrid";
import { set } from "idb-keyval";

export default {
  name: "FileRender",
  components: {
    LoadingIndicator,
    /*     VideoPlayer,
     */
  },
  props: {
    previewEntity: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      preview: {
        loading: true,
        error: null,
        url: "",
      },
      videoOptions: {
        autoplay: true,
        controls: true,
        fluid: true,
        responsive: true,
        sources: [
          {
            src: "",
            type: "",
          },
        ],
      },
      textFileContent: "",
      isPdf: this.previewEntity.mime_type === "application/pdf",
      isImage: this.previewEntity.mime_type?.startsWith("image/"),
      isVideo: this.previewEntity.mime_type?.startsWith("video/"),
      isFrappeDoc: this.previewEntity.mime_type === "frappe_doc",
      isTxt:
        this.previewEntity.mime_type?.startsWith("text/") ||
        this.previewEntity.mime_type === "application/json" ||
        this.previewEntity.mime_type === "application/javascript" ||
        this.previewEntity.mime_type === "text/x-python",
      isDocx:
        this.previewEntity.mime_type ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      isXlsx:
        this.previewEntity.mime_type ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    };
  },
  watch: {
    previewEntity() {
      this.renderContent();
    },
  },
  created() {
    this.$options.gridData = [];
  },
  mounted() {
    this.renderContent();
  },
  methods: {
    renderContent() {
      set(this.previewEntity.name, Date.now());
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
        this.preview.error = "Previews are not supported for this file type";
        this.preview.loading = false;
      } else if (this.previewEntity.size_in_bytes > 1000 * 2048 * 2048) {
        // Size limit = 400
        this.preview.error = "File is too large to preview";
        this.preview.loading = false;
      } else if (this.isVideo) {
        /*  this.preview.url = `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`  */
        this.videoOptions.sources[0].src = `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`;
        this.videoOptions.sources[0].type = this.previewEntity.mime_type;
        if (this.previewEntity.mime_type !== "video/webm" || "video/mp4") {
          /* Take a gamble its a valid H264/H265 file*/
          this.videoOptions.sources[0].type = "video/mp4";
        }
        this.preview.loading = false;
      } else {
        this.fetchContent();
      }
    },
    async fetchContent() {
      const headers = {
        Accept: "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "X-Frappe-Site-Name": window.location.hostname,
        Range: "bytes=0-10000000",
      };
      const res = await fetch(
        `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`,
        {
          method: "GET",
          headers,
        }
      );
      if (res.ok) {
        const blob = await res.blob();
        this.preview.url = URL.createObjectURL(blob);
        if (this.isTxt) {
          let data = await blob.text();
          this.textFileContent = data;
        }
        if (this.isDocx) {
          docx.renderAsync(
            blob,
            document.getElementById("container"),
            document.getElementById("container"),
            {
              ignoreLastRenderedPageBreak: false,
              experimental: true,
            }
          );
          //.then((x) => console.log("docx: finished"));
        } else if (this.isXlsx) {
          const z = await blob.arrayBuffer();
          const wb = read(z);
          this.$options.gridData = utils.sheet_to_json(
            wb.Sheets[wb.SheetNames[0]]
          );
          //Object.freeze(this.$options.gridData);
          const grid = canvasDatagrid({
            parentNode: document.getElementById("gridctr"),
            data: this.$options.gridData,
          });
          grid.style.height = "100%";
          grid.style.width = "100%";
        }
        this.preview.loading = false;
      } else {
        this.preview.error = "No preview available";
        this.preview.loading = false;
      }
    },
  },
};
</script>
