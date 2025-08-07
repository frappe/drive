<template>
  <Combobox
    :options="OPTIONS"
    v-model="selected"
    placeholder="Font Family"
    class="min-w-[10rem]"
  />
</template>
<script setup lang="ts">
import { Combobox } from "frappe-ui"
import { ref, watchEffect, watch } from "vue"

const props = defineProps({
  editor: Object,
})

const OPTIONS = [
  {
    label: "Caveat",
    value: "caveat",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-caveat)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-caveat)",
      }),
  },
  {
    label: "Comic Sans",
    value: "comic-sans",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-comic-sans)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-comic-sans)",
      }),
  },
  {
    label: "Comfortaa",
    value: "comfortaa",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-comfortaa)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-comfortaa)",
      }),
  },
  {
    label: "EB Garamond",
    value: "eb-garamond",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-eb-garamond)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-eb-garamond)",
      }),
  },
  {
    label: "Fantasy",
    value: "fantasy",
    action: (editor) => editor.chain().focus().setFontFamily("fantasy").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "fantasy",
      }),
  },
  {
    label: "Geist Mono",
    value: "geist",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-geist)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-geist)",
      }),
  },
  {
    label: "IBM Plex Sans",
    value: "ibm-plex",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-ibm-plex)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-ibm-plex)",
      }),
  },
  {
    label: "Inter",
    value: "inter",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-inter)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-inter)",
      }),
  },
  {
    label: "JetBrains Mono",
    value: "jetbrains",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-jetbrains)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-jetbrains)",
      }),
  },
  {
    label: "Lora",
    value: "lora",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-lora)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-lora)",
      }),
  },
  {
    label: "Merriweather",
    value: "merriweather",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-merriweather)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-merriweather)",
      }),
  },
  {
    label: "Nunito",
    value: "nunito",
    action: (editor) =>
      editor.chain().focus().setFontFamily("var(--font-nunito)").run(),
    isActive: (editor) =>
      editor.isActive("textStyle", {
        fontFamily: "var(--font-nunito)",
      }),
  },
]
const selected = ref(OPTIONS.find((opt) => opt.isActive(props.editor))?.value)
watchEffect(() => {
  selected.value = OPTIONS.find((opt) => opt.isActive(props.editor))?.value
})

// When user selects a new font
watch(selected, (val) => {
  if (val) OPTIONS.find((k) => k.value === val).action(props.editor)
})
</script>
