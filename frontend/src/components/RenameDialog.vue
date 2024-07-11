<template>
  <Dialog v-model="open" :options="{ title: 'Rename', size: 'xs' }">
    <template #body-content>
      <div class="flex items-center justify-center">
        <Input
          ref="input"
          v-model="newName"
          class="w-full"
          type="text"
          @keyup.enter="$resources.rename.submit"
        />
        <span
          v-if="entity.file_ext"
          :variant="'subtle'"
          theme="gray"
          size="sm"
          class="form-input font-medium ml-2 text-gray-700 border-gray-100"
        >
          {{ entity.file_ext.toUpperCase().slice(1) }}
        </span>
      </div>
      <ErrorMessage class="mt-2" :message="errorMessage" />
      <div class="flex mt-8">
        <Button
          variant="solid"
          class="w-full"
          :loading="$resources.rename.loading"
          @click="$resources.rename.submit"
        >
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { ref } from "vue"
import { Dialog, Input, ErrorMessage, Badge } from "frappe-ui"
import { useFocus } from "@vueuse/core"
import { useRoute } from "vue-router"
import { useStore } from "vuex"
import { toast } from "../utils/toasts.js"

export default {
  name: "RenameDialog",
  components: {
    Dialog,
    Input,
    ErrorMessage,
    Badge,
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
  setup(props) {
    const newName = ref("")
    const route = useRoute()
    const store = useStore()
    let parsedName = ""
    if (props.entity?.is_group || props.entity?.document) {
      newName.value = props.entity.title
      if (route.meta.documentPage) {
        store.state.entityInfo[0].title = newName.value
      }
    } else {
      parsedName = props.entity?.title.split(".").slice(0, -1).join(".")
    }
    newName.value = parsedName?.length > 1 ? parsedName : props.entity?.title
    const input = ref()
    const { focused } = useFocus(input, { initialValue: true })
    return {
      input,
      focused,
      newName,
    }
  },
  data() {
    return {
      errorMessage: "",
      extension: "",
    }
  },
  computed: {
    entityName() {
      return this.entity?.name
    },
    fullName() {
      let trimmed_name = this.newName.trim()
      if (this.entity?.file_ext) {
        return trimmed_name + this.entity.file_ext
      } else {
        return trimmed_name
      }
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit("update:modelValue", value)
        if (!value) {
          this.newName = ""
          this.errorMessage = ""
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
          toast({
            title: `Renamed ${this.$store.state.entityInfo[0].title} to ${this.newName}`,
            position: "bottom-right",
            timeout: 2,
          })
          this.$store.state.entityInfo[0].title = data.title
          this.$store.state.passiveRename = false
          this.$emit("success", data)
          this.newName = ""
          this.extension = ""
          this.errorMessage = ""
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
