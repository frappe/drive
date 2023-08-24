<template>
  <Dialog v-model="open" :options="{ title: 'Rename', size: 'xs' }">
    <template #body-content>
      <Input v-model="newName" type="text" />
      <ErrorMessage class="mt-2" :message="errorMessage" />
      <div class="flex mt-8">
        <Button
          variant="solid"
          class="w-full"
          :loading="$resources.rename.loading"
          @click="performRename">
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { Dialog, Input, ErrorMessage } from "frappe-ui";

export default {
  name: "RenameDialog",
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
    entity: {
      type: Object,
      required: false,
      default: null,
    },
  },
  emits: ["update:modelValue", "success"],
  data() {
    return {
      newName: "",
      errorMessage: "",
      extension: "",
    };
  },
  computed: {
    entityName() {
      return this.entity?.name;
    },
    open: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
        if (!value) {
          this.newName = "";
          this.errorMessage = "";
        }
      },
    },
    fileName() {
      if (this.entity?.title) {
        const parts = this.entity.title.split(".");
        parts.pop();
        return parts.join(".") ? parts.join(".") : this.entity?.title;
      }
    },
  },
  methods: {
    addExtension(newName) {
      if (this.entity) {
        const extension = this.entity.title.split(".").pop();
        return `${newName}.${extension}`;
      }
      return newName;
    },
    performRename() {
      const trimmedName = this.newName.trim();
      if (this.entity.is_group || this.entity.document) {
        this.$resources.rename.submit({
          method: "rename",
          entity_name: this.entityName,
          new_title: trimmedName,
        });
      } else {
        const newTitle = this.addExtension(trimmedName);
        this.$resources.rename.submit({
          method: "rename",
          entity_name: this.entityName,
          new_title: newTitle,
        });
      }
    },
  },
  updated() {
    this.newName = this.fileName;
  },
  resources: {
    rename() {
      return {
        url: "drive.api.files.call_controller_method",
        params: {
          method: "rename",
          entity_name: this.entityName,
          new_title: this.newName,
        },
        validate(params) {
          if (!params?.new_title) {
            return "New name is required";
          }
        },
        onSuccess(data) {
          this.newName = "";
          this.errorMessage = "";
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
