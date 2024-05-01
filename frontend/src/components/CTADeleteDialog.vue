<template>
  <Dialog v-model="open" :options="{ title: title, size: 'sm' }">
    <template #body-content>
      <p class="text-gray-600">
        {{ message }}
      </p>
      <div class="flex mt-5">
        <Button
          :variant="buttonVariant"
          theme="red"
          icon-left="trash-2"
          class="w-full"
          :loading="$resources.action.loading"
          @click="$resources.action.submit()"
        >
          {{ buttonText }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog } from "frappe-ui"

export default {
  name: "CTADeleteDialog",
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
    clearAll: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ["update:modelValue", "success"],
  data: () => ({
    title: "",
    message: "",
    buttonText: "",
    buttonVariant: "subtle",
    url: null,
  }),
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
  mounted() {
    this.evalDialog()
  },
  methods: {
    evalDialog() {
      if (this.$route.name === "Recents") {
        this.title = "Clear Recents?"
        this.message = "All your recently viewed files will be cleared"
        this.buttonText = "Clear"
        this.url = "drive.api.files.remove_recents"
      }
      if (this.$route.name === "Favourites") {
        this.title = "Clear Favourites?"
        this.message =
          "All your favourited items will be marked as unfavourite."
        this.buttonText = "Unfavourite"
        this.url = "drive.api.files.add_or_remove_favourites"
      }
      if (this.$route.name === "Trash") {
        this.title = "Delete Forever?"
        this.message =
          "All items in your Trash will be deleted forever. This is an irreversible process."
        this.buttonVariant = "solid"
        this.buttonText = "Delete"
        this.url = "drive.api.files.delete_entities"
      }
    },
  },
  resources: {
    action() {
      return {
        url: this.url,
        params: {
          clear_all: true,
        },
        onSuccess(data) {
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
