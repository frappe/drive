<template>
  <Dialog v-model="open" :options="{ title: 'Rename', size: 'xs' }">
    <template #body-content>
      <div class="flex items-center justify-center">
        <Input
          ref="input"
          class="w-full"
          v-model="newName"
          type="text"
          @keyup.enter="$resources.rename.submit" />
        <Badge
          v-if="entity.file_ext"
          :variant="'subtle'"
          theme="gray"
          size="sm"
          class="ml-2"
          :label="entity.file_ext"></Badge>
      </div>
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
import { Dialog, Input, ErrorMessage, Badge } from "frappe-ui";
import { useFocus } from "@vueuse/core";
import { formatSize, formatDate } from "@/utils/format";

export default {
  name: "RenameDialog",
  components: {
    Dialog,
    Input,
    ErrorMessage,
    Badge,
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
    };
  },
  computed: {
    entityName() {
      return this.entity?.name;
    },
    fullName() {
      if (this.entity?.file_ext) {
        return this.newName + this.entity.file_ext;
      } else {
        return this.newName;
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
  resources: {
    rename() {
      return {
        url: "drive.api.files.call_controller_method",
        method: "POST",
        params: {
          method: "rename",
          entity_name: this.entityName,
          new_title: this.fullName,
        },
        onSuccess(data) {
          this.newName = "";
          this.extension = "";
          this.errorMessage = "";
          data.size_in_bytes = data.file_size;
          data.file_size = formatSize(data.file_size);
          data.modified = formatDate(data.modified);
          data.creation = formatDate(data.creation);
          data.owner =
            data.owner === this.$store.state.auth.user_id ? "Me" : entity.owner;
          data.is_group
            ? this.$store.commit("setCurrentFolder", [data])
            : this.$store.commit("setEntityInfo", [data]);
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
  created() {
    this.newName = this.entity?.title.split(".").slice(0, -1).join(".");
  },
};
</script>
