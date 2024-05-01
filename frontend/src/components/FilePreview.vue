<template>
  <Teleport to="#modals">
    <div class="fixed inset-0 flex items-center justify-center px-4 py-4 z-10">
      <div
        class="fixed inset-0 transition-opacity bg-gray-900 opacity-75"
        @click="$emit('hide')"
      ></div>
      <FileRender :preview-entity="previewEntity" />
    </div>
  </Teleport>
</template>

<script>
import FileRender from "@/components/FileRender.vue"
import { Teleport } from "vue"
export default {
  name: "FilePreview",
  components: {
    FileRender,
    Teleport,
  },
  props: {
    previewEntity: {
      type: Object,
      required: true,
    },
  },
  emits: ["hide"],
  mounted() {
    this.escapeListener = (e) => {
      if (e.key === "Escape") {
        this.$emit("hide")
      }
    }
    document.addEventListener("keydown", this.escapeListener)
  },
  unmounted() {
    document.removeEventListener("keydown", this.escapeListener)
  },
}
</script>
