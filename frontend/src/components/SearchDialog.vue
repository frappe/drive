<template>
  <Dialog :options="{title: 'Search in Drive'}" v-model="open">
    <template #body-content>
      <Input iconLeft="search" type="text" v-model="search" placeholder="Search in Drive" />
      <div>{{$resources.entities.data.map(x=> x.title)}}</div>
      <ErrorMessage class="mt-2" :message="errorMessage" />
    </template>
  </Dialog>
</template>
<script>
import { Dialog, Input, ErrorMessage } from 'frappe-ui'
import { formatSize, formatDate } from '@/utils/format'

export default {
  name: 'SearchDialog',
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
  },
  emits: ['update:modelValue'],
  data() {
    return {
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
        if (!value) {
          this.errorMessage = ''
        }
      },
    },
  },
  resources: {
    entities() {
      return {
        method: 'drive.api.permissions.get_all_my_entities',
        onSuccess(data) {
          this.$resources.entities.error = null
          data.forEach((entity) => {
            entity.size_in_bytes = entity.file_size
            entity.file_size = entity.is_group
              ? '-'
              : formatSize(entity.file_size)
            entity.modified = formatDate(entity.modified)
            entity.creation = formatDate(entity.creation)
            entity.owner = entity.owner === this.userId ? 'Me' : entity.owner
          })
        },
        auto: true,
      }
    },
  },
}
</script>

