<template>
  <div class="flex gap-2">
    <Combobox
      :options="FONT_SIZES"
      v-model="size"
      :placeholder="font_size + 'px'"
      :open-on-click="true"
      class="w-[5rem]"
    />
    <Combobox
      :options="FONT_FAMILIES"
      v-model="selected"
      :placeholder="FONT_FAMILIES.find((k) => k.value === font_family)?.label"
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
  font_size: Number,
  font_family: String,
})

const STATIC_FONTS = [
  { value: "6px" },
  { value: "10px" },
  { value: "12px" },
  { value: "14px" },
  { value: "15px" },
  { value: "16px" },
  { value: "17px" },
  { value: "18px" },
  { value: "19px" },
  { value: "20px" },
  { value: "24px" },
  { value: "30px" },
  { value: "48px" },
  { value: "60px" },
  { value: "92px" },
]

const FONT_SIZES = [
  {
    type: "custom",
    label: "Clear",
    onClick: props.editor.commands.unsetFontSize,
  },
  ...STATIC_FONTS.map((k) => ({ value: k.value, label: k.value })),
  // Add custom
]

const selected = ref(null)
const size = ref(null)

watchEffect(() => {
  selected.value = FONT_FAMILIES.find((opt) =>
    opt.isActive(props.editor)
  )?.value
  size.value = STATIC_FONTS.find((opt) =>
    props.editor.isActive("textStyle", {
      fontSize: opt.value,
    })
  )?.value
})

watch(selected, (val) => {
  if (val) FONT_FAMILIES.find((k) => k.value === val).action(props.editor)
})
watch(size, (val) => {
  props.editor.commands.setFontSize(val)
})
</script>
