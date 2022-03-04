<template>
  <portal to="modals">
    <div class="fixed inset-0 flex items-center justify-center px-4 py-4">
      <div
        class="fixed inset-0 transition-opacity bg-gray-900 opacity-75"
        @click="this.$emit('hide')"
      ></div>
      <img
        v-if="isImage"
        :src="previewUrl"
        class="object-contain max-h-[95vh] max-w-[80vw] z-10"
      />
      <div
        v-else
        class="max-h-[95vh] max-w-[80vw] z-10 bg-[#252728] rounded-lg shadow-xl"
      >
        <object class="w-full min-w-[80vw] h-[95vh]" :data="previewUrl" />
      </div>
    </div>
  </portal>
</template>
<script>
export default {
  name: 'FilePreview',
  props: {
    previewEntity: {
      type: Object,
      required: true,
    },
  },
  emits: ['hide'],
  computed: {
    previewUrl() {
      return `/api/method/drive.api.files.get_file_content?entity_name=${this.previewEntity.name}`
    },
    isImage() {
      return this.previewEntity.mime_type.startsWith('image/')
    },
  },
  mounted() {
    this.escapeListener = (e) => {
      if (e.key === 'Escape') {
        this.$emit('hide')
      }
    }
    document.addEventListener('keydown', this.escapeListener)
  },
  unmounted() {
    document.removeEventListener('keydown', this.escapeListener)
  },
}
</script>
