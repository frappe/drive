<template>
  <div>
    <Dialog
      v-for="dialog in dialogs"
      :key="dialog.key"
      v-model="dialog.modelValue"
      :options="dialog.options"
      @close="dialog.remove"
    >
      <template
        v-if="dialog.options.component"
        #body-content
      >
        <component :is="dialog.options.component" />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { useDialogs } from "@/utils/dialogs"
import { Dialog } from "frappe-ui"

const dialogs = useDialogs()
</script>
