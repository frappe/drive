<template>
  <Dialog :options="{ title: ' ' }" v-model="open">
    <template #body-content>
      <div class="text-2xl font-medium">{{ entity.title }}</div>
      <div class="grid grid-cols-[2fr_1fr] grid-rows-2 gap-5 mt-6 antialiased">
        <div
          class="grid grid-cols-[auto_1fr] items-center grid-rows-3 gap-x-1.5 text-base text-gray-600"
        >
          <FeatherIcon
            name="clock"
            :strokeWidth="2"
            class="w-4 h-4 row-span-1 text-gray-700"
          />
          <p class="font-medium text-gray-700">History</p>
          <div class="row-span-2"></div>
          <div>Modified: {{ entity.modified }}</div>
          <div>Created: {{ entity.creation }}</div>
        </div>
        <div
          class="grid grid-cols-[auto_1fr] items-center grid-rows-3 gap-x-1.5 text-base text-gray-600"
        >
          <FeatherIcon
            name="pie-chart"
            :strokeWidth="2"
            class="w-4 h-4 row-span-1 text-gray-700"
          />
          <p class="font-medium text-gray-700">Size</p>
          <div class="row-span-2"></div>
          <div>{{ entity.file_size }}</div>
        </div>
        <div
          class="grid grid-cols-[auto_1fr] items-center grid-rows-3 gap-x-1.5 text-base text-gray-600"
        >
          <FeatherIcon
            name="user"
            :strokeWidth="2"
            class="w-4 h-4 row-span-1 text-gray-700"
          />
          <p class="font-medium text-gray-700">Owner</p>
          <div class="row-span-2"></div>
          <div>{{ entity.owner }}</div>
        </div>
        <div
          class="grid grid-cols-[auto_1fr] items-center grid-rows-3 gap-x-1.5 text-base text-gray-600"
        >
          <FeatherIcon
            name="tag"
            :strokeWidth="2"
            class="w-4 h-4 row-span-1 text-gray-700"
          />
          <p class="font-medium text-gray-700">Type</p>
          <div class="row-span-2"></div>
          <div v-if="entity.is_group">folder</div>
          <div v-else>{{ entity.mime_type || 'unknown' }}</div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { Dialog, FeatherIcon } from 'frappe-ui'

export default {
  name: 'DetailsDialog',
  components: {
    Dialog,
    FeatherIcon,
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
  emits: ['update:modelValue'],
  computed: {
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
}
</script>
