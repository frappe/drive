<template>
  <NewDialog :options="{ title: 'New Folder' }" v-model="open">
    <template #dialog-content>
      <Input
        type="text"
        v-model="folderName"
        placeholder="Folder Name"
        @keydown.enter="
          (e) =>
            $resources.createFolder.submit({
              title: e.target.value.trim(),
              parent,
            })
        "
      />
      <ErrorMessage class="mt-2" :message="errorMessage" />
    </template>
    <template #dialog-actions>
      <Button
        type="primary"
        @click="$resources.createFolder.submit()"
        :loading="$resources.createFolder.loading"
      >
        Create
      </Button>
      <Button @click="open = false"> Cancel </Button>
    </template>
  </NewDialog>
</template>
<script>
import { NewDialog, Input, ErrorMessage } from 'frappe-ui'

export default {
  name: 'NewFolderDialog',
  components: {
    NewDialog,
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
      default: '',
    },
  },
  emits: ['success'],
  data() {
    return {
      folderName: '',
      errorMessage: '',
    }
  },
  computed: {
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
  },
  unmounted() {
    this.folderName = ''
    this.errorMessage = ''
  },
  resources: {
    createFolder() {
      return {
        method: 'drive.api.files.create_folder',
        params: {
          title: this.folderName,
          parent: this.parent,
        },
        validate(params) {
          if (!params?.title) {
            return 'Folder name is required'
          }
        },
        onSuccess(data) {
          this.folderName = ''
          this.$emit('success', data)
        },
        onError(error) {
          if (error.messages) {
            this.errorMessage = error.messages.join('\n')
          } else {
            this.errorMessage = error.message
          }
        },
      }
    },
  },
}
</script>
