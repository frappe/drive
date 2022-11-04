<template>
  <portal to="modals">
    <div class="fixed inset-0 flex items-center justify-center px-4 py-4 z-10">
      <div class="fixed inset-0 transition-opacity bg-gray-900 opacity-75" @click="this.$emit('hide')"></div>
      <FileRender :previewEntity="previewEntity" />
    </div>
  </portal>
</template>

<script>
import FileRender from '@/components/FileRender.vue'
export default {
  name: 'FilePreview',
  components: {
    FileRender,
  },
  props: {
    previewEntity: {
      type: Object,
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