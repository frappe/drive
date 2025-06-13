<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Add Video' }"
    @after-leave="reset"
  >
    <template #body-content>
      <FileUploader
        file-types="video/*"
        @success="(file) => (addVideoDialog.url = file.file_url)"
      >
        <template #default="{ file, progress, uploading, openFileSelector }">
          <div class="flex items-center space-x-2">
            <Button @click="openFileSelector">
              {{
                uploading
                  ? `Uploading ${progress}%`
                  : addVideoDialog.url
                  ? "Change Video"
                  : "Upload Video"
              }}
            </Button>
            <Button
              v-if="addVideoDialog.url"
              @click="
                () => {
                  addVideoDialog.url = null
                  addVideoDialog.file = null
                }
              "
            >
              Remove
            </Button>
          </div>
        </template>
      </FileUploader>
      <video
        v-if="addVideoDialog.url"
        :src="addVideoDialog.url"
        class="mt-2 w-full rounded-lg"
        type="video/mp4"
      />
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="mr-2"
        @click="addVideo(addVideoDialog.url)"
      >
        Insert Video
      </Button>
      <Button @click="reset"> Cancel </Button>
    </template>
  </Dialog>
</template>
<script>
import { Button, Dialog, FileUploader } from "frappe-ui"

export default {
  name: "InsertImage",
  components: { Button, Dialog, FileUploader },
  props: {
    modelValue: {
      type: Boolean,
      required: false,
    },
    editor: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      addVideoDialog: { url: "", file: null },
    }
  },
  computed: {
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
        if (!value) {
          this.errorMessage = ""
        }
      },
    },
  },
  methods: {
    onVideoSelect(e) {
      let file = e.target.files[0]
      if (!file) {
        return
      }
      this.addVideoDialog.file = file
    },
    addVideo(src) {
      this.editor
        .chain()
        .focus()
        .setMedia({
          src: src,
          "media-type": "video",
          width: "100%",
          height: "auto",
        })
        .run()
      this.reset()
    },
    reset() {
      this.open = false
    },
  },
}
</script>
