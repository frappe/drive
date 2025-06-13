<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Add Image' }"
    @after-leave="reset"
  >
    <template #body-content>
      <FileUploader
        file-types="image/*"
        @success="(file) => (addImageDialog.url = file.file_url)"
      >
        <template #default="{ file, progress, uploading, openFileSelector }">
          <div class="flex items-center space-x-2">
            <Button @click="openFileSelector">
              {{
                uploading
                  ? `Uploading ${progress}%`
                  : addImageDialog.url
                  ? "Change Image"
                  : "Upload Image"
              }}
            </Button>
            <Button
              v-if="addImageDialog.url"
              @click="
                () => {
                  addImageDialog.url = null
                  addImageDialog.file = null
                }
              "
            >
              Remove
            </Button>
          </div>
        </template>
      </FileUploader>
      <img
        v-if="addImageDialog.url"
        :src="addImageDialog.url"
        class="mt-2 w-full rounded-lg space-x-2"
      />
    </template>
    <template #actions>
      <Button
        class="mr-2"
        variant="solid"
        @click="addImage(addImageDialog.url)"
      >
        Insert Image
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
      addImageDialog: { url: "", file: null },
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
    onImageSelect(e) {
      let file = e.target.files[0]
      if (!file) {
        return
      }
      this.addImageDialog.file = file
    },

    addImage(src) {
      this.editor
        .chain()
        .focus()
        .setMedia({
          src: src,
          "media-type": "img",
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
