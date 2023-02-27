<template>
  <LoadingIndicator
    v-if="preview.loading"
    class="w-10 h-10 z-10 text-neutral-100 mx-auto"
  />
  <div
    v-else-if="preview.error"
    class="p-8 z-10 bg-[#252728] rounded-md text-neutral-100 text-xl text-center font-medium"
  >
    {{ preview.error }}
  </div>
  
  <img
    v-if="isImage"
    :src="preview.url"
    class="object-contain max-h-[95vh] max-w-[80vw] z-10"
  />
  <div
    v-if="isDocx"
    id="container"
    class="object-contain max-h-[95vh] max-w-[80vw] z-10 overflow-y-scroll"
  ></div>
  <div
    v-if="isPdf"
    class="max-h-[95vh] max-w-[75vw] z-10 bg-[#252728] rounded-lg shadow-xl">
    <iframe class="w-full min-w-[75vw] h-[90vh]" :src="preview.url" />
  </div>
</template>
<script>
import { LoadingIndicator } from 'frappe-ui';
import * as docx from 'docx-preview';
import { set } from 'idb-keyval'


export default {
  name: 'FileRender',
  components: {
    LoadingIndicator,
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
        url: '',
      },
      isPdf: this.previewEntity.mime_type === 'application/pdf',
      isImage: this.previewEntity.mime_type?.startsWith('image/'),
      isDocx:
        this.previewEntity.mime_type ===
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    };
  },
  mounted() {
    this.renderContent();
  },
  watch: {
    previewEntity() {
      this.renderContent();
    },
  },
  methods: {
    renderContent() {
      set(this.previewEntity.name, Date.now())
      const isSupportedType =
        this.previewEntity.mime_type &&
        [
          'image',
          'video',
          'application/pdf',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ].some((type) => this.previewEntity.mime_type.startsWith(type));
      if (!isSupportedType) {
        this.preview.error = 'Previews are not supported for this file type';
        this.preview.loading = false;
      } else if (this.previewEntity.size_in_bytes > 100 * 2048 * 2048) {
        // Size limit = 400
        this.preview.error = 'File is too large to preview';
        this.preview.loading = false;
      } else {
        this.fetchContent();
      }
    },
    async fetchContent() {
      const headers = {
        Accept: 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'X-Frappe-Site-Name': window.location.hostname,
      };
      const res = await fetch(
        `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`,
        {
          method: 'GET',
          headers,
        }
      );

      if (res.ok) {
        const blob = await res.blob();
        this.preview.url = URL.createObjectURL(blob);
        this.preview.loading = false;
        if (
          this.previewEntity.mime_type ===
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ) {
          docx
            .renderAsync(
              blob,
              document.getElementById('container'),
              document.getElementById('container'),
              {
                ignoreLastRenderedPageBreak: false,
                experimental: true,
              }
            )
            .then((x) => console.log('docx: finished'));
        }
      } else {
        this.preview.error = 'No preview available';
        this.preview.loading = false;
      }
    },
  },
};
</script>
