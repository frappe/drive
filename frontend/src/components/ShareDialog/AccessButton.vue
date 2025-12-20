<template>
  <div class="flex gap-1">
    <Dropdown
      :button="{
        label: shareAccess === 'editor' ? __('Can edit') : __('Can view'),
        iconRight: 'chevron-down',
        variant: 'ghost',
      }"
      placement="right"
      :options="[
        {
          value: 'reader',
          label: __('Can view'),
          onClick: () => (shareAccess = 'reader'),
          icon: shareAccess === 'reader' && 'check',
        },
        {
          value: 'editor',
          label: __('Can edit'),
          onClick: () => (shareAccess = 'editor'),
          icon: shareAccess === 'editor' && 'check',
        },
        {
          group: true,
          hideLabel: true,
          items: [
            {
              label: __('Remove'),
              onClick: () => emit('removeAccess'),
              theme: 'red',
            },
          ],
        },
      ]"
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
