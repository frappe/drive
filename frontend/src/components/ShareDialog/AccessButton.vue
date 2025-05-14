<template>
  <div class="flex gap-2">
    <Autocomplete
      class="w-fit"
      placeholder="Access"
      v-model="shareAccess"
      :options="[
        { value: 'reader', label: 'Reader' },
        { value: 'editor', label: 'Editor' },
      ]"
      :hideSearch="true"
    ></Autocomplete>
    <Button variant="ghost" @click="$emit('removeAccess')"
      ><LucideX class="size-4 my-auto"
    /></Button>
  </div>
</template>
<script setup>
import { Autocomplete } from "frappe-ui"
import { ref } from "vue"

const props = defineProps({ accessLevels: Object, accessObj: Object })
const shareAccess = ref(props.accessObj.write ? "editor" : "reader")

defineEmits(["updateAccess", "removeAccess"])
</script>
