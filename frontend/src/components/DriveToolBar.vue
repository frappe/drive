<template>
  <div
    class="mb-4 min-h-8 py-2 flex gap-3 flex-wrap justify-between items-center w-full px-5 sm:px-0"
  >
    <Breadcrumbs :breadcrumbLinks="breadcrumbs" />
    <Button type="primary"> Upload </Button>
  </div>
</template>

<script>
import { Button } from 'frappe-ui'
import Breadcrumbs from '@/components/Breadcrumbs.vue'

export default {
  name: 'DriveToolBar',
  components: {
    Button,
    Breadcrumbs,
  },
  props: {
    breadcrumbs: {
      type: Array,
      required: true,
    },
  },
}
</script>
