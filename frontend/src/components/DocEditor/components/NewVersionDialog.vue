<template>
  <FormControl
    v-focus
    v-model="versionName"
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
    @click="emitter.emit('create-version', versionName), (dialogs = [])"
    :disabled="!versionName"
  />
</template>
<script setup>
import { ref } from "vue"
import { useDialogs } from "@/utils/dialogs"
import LucideVersion from "~icons/lucide/git-pull-request-create"
import emitter from "@/emitter"

const versionName = ref("")

const dialogs = useDialogs()
</script>
