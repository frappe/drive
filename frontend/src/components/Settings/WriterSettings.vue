<template>
  <div class="flex items-center mb-4">
    <h1 class="font-semibold text-ink-gray-9">
      {{ __("Writer") }}
    </h1>
  </div>
  <div class="overflow-y-auto ps-1">
    <div class="flex flex-col gap-4 pb-5 pr-5">
      {{ settings }}
      <FormControl
        type="select"
        label="Font Family"
        :options="fontFamilyOptions"
        v-model="settings.font_family"
        description="Choose the font family for the editor."
      />
      <FormControl
        type="select"
        label="Font Size"
        :options="fontSizeOptions"
        v-model="settings.font_size"
        description="Set the font size (px)."
      />
      <FormControl
        type="select"
        label="Line Height"
        :options="lineHeightOptions"
        v-model="settings.line_height"
        description="Set the line height."
      />
      <FormControl
        label="Custom Classes"
        placeholder="font-lg"
        v-model="settings.custom_css"
        description="Any additional classes to apply to the editor."
        type="textarea"
      />
      <!-- <Button
        label="Update"
        variant="solid"
        :disabled="!edited"
        :loading="updateSettings.isLoading"
        @click="updateSettings.submit()"
        class="mt-4"
      /> -->
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from "vue"
import { FormControl, useDoc } from "frappe-ui"
import { useStore } from "vuex"

const store = useStore()

const fontFamilyOptions = [
  { label: "Inter", value: "Inter" },
  { label: "Serif", value: "serif" },
  { label: "Monospace", value: "monospace" },
  { label: "Sans-serif", value: "sans-serif" },
  { label: "Georgia", value: "Georgia" },
  { label: "Arial", value: "Arial" },
  { label: "Times New Roman", value: "Times New Roman" },
]

const fontSizeOptions = [
  { label: "13px", value: 14 },
  { label: "14px", value: 14 },
  { label: "15px", value: 15 },
  { label: "16px", value: 16 },
  { label: "17px", value: 17 },
  { label: "18px", value: 18 },
]

const lineHeightOptions = [
  { label: "1.2", value: "1.2" },
  { label: "1.4", value: "1.4" },
  { label: "1.5", value: "1.5" },
  { label: "1.6", value: "1.6" },
  { label: "1.8", value: "1.8" },
  { label: "2", value: "2" },
  { label: "2.5", value: "2.2" },
  { label: "2.5", value: "2.5" },
  { label: "3", value: "3" },
]

const writerSettings = useDoc({
  doctype: "Drive Settings",
  name: store.state.user.id,
  immediate: true,
})
writerSettings.onSuccess((doc) => {
  settings.font_family = doc.font_family
  settings.font_size = doc.font_size
  settings.line_height = doc.line_height
  settings.custom_css = doc.custom_css
})
const settings = reactive({})

watch(settings, (val) => {
  console.log(val)
  //   writerSettings.setValue.submit(val)
})

// reactive({
//   font_family: "Inter",
//   font_size: "15px",
//   line_height: "1.5",
//   custom_css: "",
// })
</script>
