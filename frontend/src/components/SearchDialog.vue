<template>
  <Dialog :options="{title: 'Search in Drive'}" v-model="open">
    <template #body-content>
      <Input iconLeft="search" type="text" v-model="search" placeholder="Search in Drive"
        @input="($event) => search = $event" class="mb-2" />
      <div v-if="showEntities" v-for="entity in filteredEntities" @click="openEntity(entity)"
        class="flex flex-row cursor-pointer hover:bg-gray-100 rounded-md py-2 px-3">
        <div class="flex grow items-center">
          <img :src="`/src/assets/images/icons/${entity.is_group ? 'folder'
          : formatMimeType(entity.mime_type)}.svg`" class="w-6 mr-4" />
          <div class="w-72">
            <div class="text-lg text-gray-900 font-medium truncate">{{entity.title}}</div>
            <div class="text-[13px] text-gray-600">{{entity.owner}}</div>
          </div>
        </div>
        <div class="text-[13px] text-gray-600 whitespace-nowrap my-auto">{{entity.modified}}</div>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, Input, } from 'frappe-ui'
import { formatSize, formatDate } from '@/utils/format'
import getFilteredEntities from '../utils/fuzzySearcher'
import { formatMimeType } from '@/utils/format'

export default {
  name: 'SearchDialog',
  components: {
    Dialog,
    Input,
  },
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
  },
  emits: ['update:modelValue', 'openEntity'],
  data() {
    return {
      search: '',
    }
  },
  computed: {
    userId() {
      return this.$store.state.auth.user_id
    },
    filteredEntities() {
      return getFilteredEntities(this.search, this.$resources.entities.data)
    },
    showEntities() {
      return this.search.length > 0
    },
    open: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
  },
  methods: {
    openEntity(entity) {
      this.$emit('openEntity', entity)
      this.open = false
    },
  },
  setup() {
    return { formatMimeType }
  },
  updated() {
    this.$resources.entities.fetch()
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
            entity.owner = entity.owner === this.userId ? 'me' : entity.owner
          })
        },
        auto: true
      }
    },
  },
}
</script>

