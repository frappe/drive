<template>
  <div
    class="mb-4 min-h-8 py-2 flex gap-3 flex-wrap justify-between items-center w-full px-5 sm:px-0"
  >
    <Breadcrumbs :breadcrumbLinks="breadcrumbs" />
    <div class="flex gap-3">
      <Dropdown :items="actionItems">
        <template v-slot="{ toggleDropdown }">
          <Button
            class="text-sm focus:ring-0"
            @click.stop="toggleDropdown()"
            iconRight="chevron-down"
            >Actions</Button
          >
        </template>
      </Dropdown>
      <Button class="focus:ring-0" type="primary" @click="$emit('uploadFile')">
        Upload
      </Button>
    </div>
  </div>
</template>

<script>
import { Button, Dropdown } from 'frappe-ui'
import Breadcrumbs from '@/components/Breadcrumbs.vue'

export default {
  name: 'DriveToolBar',
  components: {
    Button,
    Breadcrumbs,
    Dropdown,
  },
  props: {
    breadcrumbs: {
      type: Array,
      required: true,
    },
    actionItems: {
      type: Array,
      required: true,
    },
  },
  emits: ['uploadFile'],
}
</script>
