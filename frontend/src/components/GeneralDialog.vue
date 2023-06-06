<template>
  <i class="fa fa-qq" aria-hidden="true"></i>
  <Dialog v-model="open" :options="{ title: dialogData.title }">
    <template #body-content>
      <p class="text-gray-600">{{ dialogData.message }}</p>
      <div class="flex mt-5">
        <Button class="ml-auto" @click="open = false">Cancel</Button>
        <Button
          :appearance="dialogData.appearance"
          :icon-left="dialogData.buttonIcon"
          class="ml-4"
          :loading="$resources.method.loading"
          @click="$resources.method.submit()">
          {{ dialogData.buttonMessage }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog } from "frappe-ui";
import { del } from "idb-keyval";

export default {
  name: "GeneralDialog",

  components: {
    Dialog,
  },

  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    entities: {
      type: [Array, String],
      required: true,
    },
    for: {
      type: String,
      default: null,
    },
  },

  emits: ["update:modelValue", "success"],

  computed: {
    dialogData() {
      const items =
        this.entities.length === 1
          ? `${this.entities.length} item`
          : `${this.entities.length} items`;
      switch (this.for) {
        case "unshare":
          return {
            title: "Remove?",
            message: "Selected items will not be shared with you anymore.",
            buttonMessage: "Remove",
            appearance: "danger",
            buttonIcon: "trash-2",
            methodName: "drive.api.files.unshare_entities",
          };
        case "restore":
          return {
            title: "Restore Items?",
            message:
              "Selected items will be restored to their original locations.",
            buttonMessage: "Restore",
            appearance: "primary",
            buttonIcon: "refresh-ccw",
            methodName: "drive.api.files.remove_or_restore",
          };
        case "remove":
          return {
            title: "Move to Trash?",
            message:
              items +
              " will be moved to Trash. Items in Trash are deleted forever after 30 days.",
            buttonMessage: "Move to Trash",
            appearance: "danger",
            buttonIcon: "trash-2",
            methodName: "drive.api.files.remove_or_restore",
          };
        default:
          return {};
      }
    },
    open: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit("update:modelValue", value);
      },
    },
  },

  resources: {
    method() {
      return {
        url: this.dialogData.methodName,
        params: {
          entity_names:
            typeof this.entities === "string"
              ? JSON.stringify([this.entities])
              : JSON.stringify(this.entities.map((entity) => entity.name)),
        },
        onSuccess(data) {
          this.$emit("success", data);
          this.$resources.method.reset();
          this.entities.map((entity) => del(entity.name));
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages);
          }
        },
      };
    },
  },
};
</script>
