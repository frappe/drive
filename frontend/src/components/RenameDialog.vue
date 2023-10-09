<template>
  <Dialog v-model="open" :options="{ title: 'Rename', size: 'xs' }">
    <template #body-content>
      <Input
        ref="input"
        v-model="newName"
        :placeholder="currentName"
        type="text"
        @keyup.enter="$resources.rename.submit" />
      <ErrorMessage class="mt-2" :message="errorMessage" />
      <div class="flex mt-8">
        <Button
          variant="solid"
          class="w-full"
          :loading="$resources.rename.loading"
          @click="$resources.rename.submit">
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { ref } from "vue";
import { Dialog, Input, ErrorMessage } from "frappe-ui";
import { useFocus } from "@vueuse/core";

export default {
  name: "RenameDialog",
  components: {
    Dialog,
    Input,
    ErrorMessage,
  },
  setup() {
    const input = ref();
    const { focused } = useFocus(input, { initialValue: true });
    return {
      input,
      focused,
    };
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
      currentName: "",
    };
  },
  computed: {
    entityName() {
      return this.entity?.name;
    },
    fullName() {
      if (this.entity?.is_group || this.entity?.document) {
        return this.newName;
      } else {
        return this.newName.slice(-1) === "."
          ? this.newName + this.extension
          : this.newName + "." + this.extension;
      }
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
  },
  watch: {
    entity: {
      handler(newVal) {
        if (newVal) {
          if (this.entity.is_group || this.entity.document) {
            this.currentName = this.entity.title;
          } else {
            // Sometimes the filename wont have an extension
            const parts = this.entity?.title.split(".");
            if (parts.length > 1) {
              this.extension = parts.pop();
              this.currentName =
                this.entity.title.substring(
                  0,
                  this.entity.title.lastIndexOf(".")
                ) || this.entity.title;
            } else {
              this.currentName = this.entity.title;
            }
          }
        }
      },
      immediate: true,
    },
  },
  resources: {
    rename() {
      return {
        //url: "drive.api.files.call_controller_method",
        url: "frappe.client.set_value",
        method: "POST",
        params: {
          doctype: "Drive Entity",
          name: this.entityName,
          fieldname: "title",
          value: this.fullName,
        },
        onSuccess(data) {
          this.newName = "";
          this.currentName = "";
          this.extension = "";
          this.errorMessage = "";
          this.$emit("success", data);
        },
        onError(error) {
          this.newName = "";
          this.currentName = "";
          this.extension = "";
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
