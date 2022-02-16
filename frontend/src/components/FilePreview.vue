<template>
  <portal to="modals">
    <div class="fixed inset-0 flex items-center justify-center px-4 py-4">
      <div
        class="fixed inset-0 transition-opacity bg-gray-900 opacity-75"
        @click="this.$emit('hide')"
      ></div>
      <div
        class="w-full transition-all transform bg-[#252728] rounded-lg shadow-xl max-h-[95vh] max-w-[80vw]"
      >
        <object
          class="w-full h-[95vh]"
          :data="`/api/method/drive.api.files.get_file_content?entity_name=${previewEntity}`"
        />
      </div>
    </div>
  </portal>
</template>
<script>
export default {
  name: 'FilePreview',
  props: {
    previewEntity: {
      type: String,
      required: true,
    },
  },
  emits: ['hide'],
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
