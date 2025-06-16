<template>
  <div class="flex gap-1">
    <Dropdown
      :button="{
        label: shareAccess === 'editor' ? 'Can edit' : 'Can view',
        iconRight: 'chevron-down',
        variant: 'ghost',
      }"
      placement="right"
      :options="[
        {
          value: 'reader',
          label: 'Can view',
          onClick: () => (shareAccess = 'reader'),
          icon: shareAccess === 'reader' && 'check',
        },
        {
          value: 'editor',
          label: 'Can edit',
          onClick: () => (shareAccess = 'editor'),
          icon: shareAccess === 'editor' && 'check',
        },
        { divider: true },
        {
          label: 'Remove',
          onClick: () => emit('removeAccess'),
          color: 'text-ink-red-3',
        },
      ]"
      :hide-search="true"
    />
  </div>
</template>
<script setup>
import { Dropdown } from "frappe-ui"
import { ref, watch } from "vue"

const props = defineProps({ accessLevels: Object, accessObj: Object })
const shareAccess = ref(props.accessObj.write ? "editor" : "reader")

watch(shareAccess, (val) =>
  emit("updateAccess", {
    read: 1,
    comment: 1,
    share: 1,
    write: val === "editor" ? 1 : 0,
  })
)

const emit = defineEmits(["updateAccess", "removeAccess"])
</script>
