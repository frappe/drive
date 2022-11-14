<template>
  <Dialog :options="{ title: 'Rename' }" v-model="open" >
    <template #body-content>
      <Input type="text" v-model="newName" placeholder="New name" @keydown.enter="
        (e) =>
          $resources.rename.submit({
            method: 'rename',
            entity_name: entityName,
            new_title: e.target.value.trim(),
          })
      " />
      <ErrorMessage class="mt-2" :message="errorMessage" />
      <div class="flex mt-8">
        <Button @click="open = false" class="ml-auto"> Cancel </Button>
        <Button appearance="primary" class="ml-4" @click="$resources.rename.submit()"
          :loading="$resources.rename.loading">
          Rename
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, Input, ErrorMessage } from 'frappe-ui'

export default {
  name: 'RenameDialog',
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
      required: true,
    },
  },
  emits: ['update:modelValue', 'success'],
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
