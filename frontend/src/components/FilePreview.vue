<template>
  <portal to="modals">
    <div class="fixed inset-0 flex items-center justify-center px-4 py-4">
      <div
        class="fixed inset-0 transition-opacity bg-gray-900 opacity-75"
        @click="this.$emit('hide')"
      ></div>
      <Spinner v-if="preview.loading" class="w-10 h-10 z-10 text-neutral-100" />
      <div
        v-else-if="preview.error"
        class="p-8 z-10 bg-[#252728] rounded-md text-neutral-100 text-xl text-center font-medium"
      >
        {{ preview.error }}
      </div>
      <img
        v-else-if="isImage"
        :src="preview.url"
        class="object-contain max-h-[95vh] max-w-[80vw] z-10"
      />
      <div
        v-else
        class="max-h-[95vh] max-w-[80vw] z-10 bg-[#252728] rounded-lg shadow-xl"
      >
        <iframe class="w-full min-w-[80vw] h-[95vh]" :src="preview.url" />
      </div>
    </div>
  </portal>
</template>
<script>
import { Spinner } from 'frappe-ui'
export default {
  name: 'FilePreview',
  components: {
    Spinner,
  },
  props: {
    previewEntity: {
      type: Object,
      required: true,
    },
  },
  emits: ['hide'],
  data() {
    return {
      preview: {
        loading: true,
        error: null,
        url: '',
      },
      isImage: this.previewEntity.mime_type?.startsWith('image/'),
    }
  },
  mounted() {
    this.escapeListener = (e) => {
      if (e.key === 'Escape') {
        this.$emit('hide')
      }
    }
    document.addEventListener('keydown', this.escapeListener)
    const isSupportedType =
      this.previewEntity.mime_type &&
      ['image', 'video', 'application/pdf'].some((type) =>
        this.previewEntity.mime_type.startsWith(type)
      )
    if (!isSupportedType) {
      this.preview.error = 'Previews are not supported for this file type'
      this.preview.loading = false
    } else if (this.previewEntity.size_in_bytes > 100 * 1024 * 1024) {
      // Size limit = 100MB
      this.preview.error = 'File is too large to preview'
      this.preview.loading = false
    } else {
      this.fetchContent()
    }
  },
  unmounted() {
    document.removeEventListener('keydown', this.escapeListener)
  },
  methods: {
    async fetchContent() {
      const headers = {
        Accept: 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'X-Frappe-Site-Name': window.location.hostname,
      }
      const res = await fetch(
        `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`,
        {
          method: 'GET',
          headers,
        }
      )
      if (res.ok) {
        const blob = await res.blob()
        this.preview.url = URL.createObjectURL(blob)
        this.preview.loading = false
      } else {
        this.preview.error = 'No preview available'
        this.preview.loading = false
      }
    },
  },
}
</script>
