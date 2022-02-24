<template>
  <NewDialog :options="{ title: 'New Folder' }" v-model="show">
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
      <Button @click="$emit('close')"> Cancel </Button>
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
    show: {
      type: Boolean,
      required: true,
    },
    parent: {
      type: String,
      default: '',
    },
  },
  emits: ['success', 'close'],
  data() {
    return {
      folderName: '',
      errorMessage: '',
    }
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
