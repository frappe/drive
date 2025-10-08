<template>
  <FormControl
    v-model="versionName"
    v-focus
    label="Name:"
  >
    <template #prefix>
      <LucideVersion class="size-4" />
    </template>
  </FormControl>
  <Button
    type="submit"
    label="Create"
    variant="solid"
    class="w-full mt-4"
    :disabled="!versionName"
    @click="emitter.emit('create-version', versionName), clearDialogs()"
  />
</template>
<script setup>
import { ref } from "vue"
import { clearDialogs } from "@/utils/dialogs"
import LucideVersion from "~icons/lucide/git-pull-request-create"
import emitter from "@/emitter"

const versionName = ref("")
</script>
