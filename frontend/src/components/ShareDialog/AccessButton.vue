<template>
  <div class="flex gap-1">
    <Dropdown :button="{
      label: shareAccess === 'editor' ? 'Can edit' : (shareAccess === 'upload' ? 'Can upload' : 'Can view'),
      iconRight: 'chevron-down',
      variant: 'ghost',
    }" placement="right" :options="dynamicList([
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
      {
        value: 'upload',
        label: 'Can upload',
        cond: props.folder,
        onClick: () => (shareAccess = 'upload'),
        icon: shareAccess === 'upload' && 'check',
      },
      {
        group: true,
        hideLabel: true,
        items: [
          {
            label: 'Remove',
            onClick: () => emit('removeAccess'),
            theme: 'red',
          },
        ],
      },
    ])" />
  </div>
</template>
<script setup>
import { Dropdown } from "frappe-ui"
import { ref, watch } from "vue"
import { dynamicList } from "@/utils/files"


const props = defineProps({ accessLevels: Object, accessObj: Object, folder: Boolean })
const shareAccess = ref(props.accessObj.write ? "editor" : "reader")

watch(shareAccess, (val) =>
  emit("updateAccess", {
    read: 1,
    comment: 1,
    share: 1,
    write: val === "editor" ? 1 : 0,
    upload: val === 'editor' || val === 'upload' ? 1 : 0
  })
)

const emit = defineEmits(["updateAccess", "removeAccess"])
</script>
