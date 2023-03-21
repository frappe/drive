<template>
  <Dialog v-model="open" :options="{ title: 'New Folder' }">
    <template #body-content>
      <Input
        v-model="folderName"
        type="text"
        placeholder="Folder Name"
        @keydown.enter="
          (e) =>
            $resources.createFolder.submit({
              title: e.target.value.trim(),
              parent,
            })
        " />
      <ErrorMessage class="mt-2" :message="errorMessage" />
    </template>
    <template #actions>
      <Button
        appearance="primary"
        :loading="$resources.createFolder.loading"
        @click="$resources.createFolder.submit()">
        Create
      </Button>
      <Button @click="open = false">Cancel</Button>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, Input, ErrorMessage } from "frappe-ui";

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
  data() {
    return {
      folderName: "",
      errorMessage: "",
    };
  },
  computed: {
    open: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
        if (!value) {
          this.folderName = "";
          this.errorMessage = "";
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
        validate(params) {
          if (!params?.title) {
            return "Folder name is required";
          }
        },
        onSuccess(data) {
          this.folderName = "";
          this.$emit("success", data);
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join("\n");
          } else {
            this.errorMessage = error.message;
          }
        },
      };
    },
  },
};
</script>
