<template>
  <div>
    <Dialog
      v-for="dialog in dialogs"
      :key="dialog.key"
      v-model:open="dialog.modelValue"
      :title="dialog.options.title"
      :message="dialog.options.message"
      :size="dialog.options.size"
      :actions="dialog.options.actions"
      @close="dialog.remove"
    >
      <component v-if="dialog.options.component" :is="dialog.options.component" />
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { useDialogs } from '@/utils/dialogs'
import { Dialog } from 'frappe-ui'

const dialogs = useDialogs()
</script>
