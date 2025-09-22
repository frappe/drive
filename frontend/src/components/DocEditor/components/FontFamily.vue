<template>
  <div>
    <Combobox
      :options="FONT_FAMILIES"
      v-model="selected"
      placeholder="Font Family"
      :open-on-click="true"
      class="min-w-[10rem]"
      :style="selected && { fontFamily: `var(--font-${selected})` }"
    />
  </div>
</template>
<script setup>
import { Combobox } from "frappe-ui"
import { ref, watchEffect, watch } from "vue"
import { FONT_FAMILIES } from "@/utils/files"

const props = defineProps({
  editor: Object,
})

const selected = ref(
  FONT_FAMILIES.find((opt) => opt.isActive(props.editor))?.value
)
watchEffect(() => {
  selected.value = FONT_FAMILIES.find((opt) =>
    opt.isActive(props.editor)
  )?.value
})

// When user selects a new font
watch(selected, (val) => {
  if (val) FONT_FAMILIES.find((k) => k.value === val).action(props.editor)
})
</script>
