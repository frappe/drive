<template>
  <Dialog v-model="open" :options="{ title: 'Delete Forever?', size: 'sm' }">
    <template #body-content>
      <p class="text-gray-600">
        {{
          entities.length === 1
            ? `${entities.length} item`
            : `${entities.length} items`
        }}
        will be deleted forever. This is an irreversible process.
      </p>
      <div class="flex mt-5">
        <Button
          variant="solid"
          theme="red"
          icon-left="trash-2"
          class="w-full"
          :loading="$resources.delete.loading"
          @click="$resources.delete.submit()"
        >
          Delete Forever
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog } from "frappe-ui"
import { del } from "idb-keyval"

export default {
  name: "DeleteDialog",
  components: {
    Dialog,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    entities: {
      type: Array,
      required: false,
      default: null,
    },
  },
  emits: ["update:modelValue", "success"],
  computed: {
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
      },
    },
  },
  resources: {
    delete() {
      return {
        url: "drive.api.files.delete_entities",
        params: {
          entity_names: JSON.stringify(
            this.entities?.map((entity) => entity.name)
          ),
        },
        onSuccess(data) {
          this.entities.map((entity) => del(entity.name))
          this.$emit("success", data)
        },
        onError(error) {
          if (error.messages) {
            console.log(error.messages)
          }
        },
      }
    },
  },
}
</script>
