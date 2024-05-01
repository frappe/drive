<template>
  <Dialog v-model="open" :options="{ title: 'New Folder', size: 'xs' }">
    <template #body-content>
      <Input
        ref="input"
        v-model="folderName"
        placeholder="Untitled Folder"
        type="text"
        @keyup.enter="
          (e) =>
            $resources.createFolder.submit({
              title: e.target.value.trim(),
              parent,
            })
        "
      />
      <ErrorMessage class="mt-2" :message="errorMessage" />
      <div class="flex mt-8">
        <Button
          variant="solid"
          class="w-full"
          :loading="$resources.createFolder.loading"
          @click="$resources.createFolder.submit()"
        >
          Create
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { ref } from "vue"
import { useFocus } from "@vueuse/core"
import { Dialog, Input, ErrorMessage } from "frappe-ui"

export default {
  name: "NewFolderDialog",
  components: {
    Dialog,
    Input,
    ErrorMessage,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    parent: {
      type: String,
      default: "",
    },
  },
  emits: ["update:modelValue", "success"],
  setup() {
    const input = ref()
    const { focused } = useFocus(input, { initialValue: true })
    return {
      input,
      focused,
    }
  },
  data() {
    return {
      folderName: "",
      errorMessage: "",
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
          this.folderName = ""
          this.errorMessage = ""
        }
      },
    },
  },
  resources: {
    createFolder() {
      return {
        url: "drive.api.files.create_folder",
        params: {
          title: this.folderName,
          parent: this.parent,
        },
        /* validate(params) {
          if (!params?.title) {
            return "Folder name is required";
          }
        }, */
        onSuccess(data) {
          this.folderName = ""
          this.$emit("success", data)
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n")
          } else {
            this.errorMessage = error.message
          }
        },
      }
    },
  },
}
</script>
