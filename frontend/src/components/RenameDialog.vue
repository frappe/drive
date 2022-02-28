<template>
  <NewDialog :options="{ title: 'Rename' }" v-model="open">
    <template #dialog-content>
      <Input
        type="text"
        v-model="newName"
        placeholder="New name"
        @keydown.enter="
          (e) =>
            $resources.rename.submit({
              method: 'rename',
              entity_name: entityName,
              new_title: e.target.value.trim(),
            })
        "
      />
      <ErrorMessage class="mt-2" :message="errorMessage" />
    </template>
    <template #dialog-actions>
      <Button
        type="primary"
        @click="$resources.rename.submit()"
        :loading="$resources.rename.loading"
      >
        Rename
      </Button>
      <Button @click="open = false"> Cancel </Button>
    </template>
  </NewDialog>
</template>
<script>
import { NewDialog, Input, ErrorMessage } from 'frappe-ui'

export default {
  name: 'RenameDialog',
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
    entity: {
      type: Object,
      required: true,
    },
  },
  emits: ['success'],
  data() {
    return {
      newName: '',
      errorMessage: '',
    }
  },
  computed: {
    entityName() {
      return this.entity?.name
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
        if (!value) {
          this.newName = ''
          this.errorMessage = ''
        }
      },
    },
  },
  resources: {
    rename() {
      return {
        method: 'drive.api.files.call_controller_method',
        params: {
          method: 'rename',
          entity_name: this.entityName,
          new_title: this.newName,
        },
        validate(params) {
          if (!params?.new_title) {
            return 'New name is required'
          }
        },
        onSuccess(data) {
          this.newName = ''
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
