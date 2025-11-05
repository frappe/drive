<template>
  <Dialog
    v-model="open"
    :options="{
      title: 'Settings',
    }"
    @close="model = false"
  >
    <template #body-content>
      <Tabs
        v-model="tabIndex"
        :tabs
      >
        <template #tab-panel>
          <div class="overflow-y-auto ps-1 pt-4">
            <Form>
              <template #default="{ dirty, setDirty, error }">
                <h3 class="text-sm font-medium text-ink-gray-7 mb-3">
                  Configuration
                </h3>
                <div class="flex flex-col gap-4 pb-5 pr-5">
                  <FormControl
                    v-model="settings.versioning"
                    type="number"
                    min="1"
                    label="Versioning Frequency"
                    placeholder="Default"
                    :options="[]"
                    :validate="
                      (k) =>
                        k >= 1
                          ? true
                          : 'Please give a positive whole number for versioning frequency.'
                    "
                    :description="`How often to take automated versions for ${
                      tabIndex === 1 ? 'this document' : 'new documents'
                    } (minutes).`"
                  />
                </div>
                <h3 class="text-sm font-medium text-ink-gray-7 mb-3">
                  Styles
                </h3>
                <div class="flex flex-col gap-4 pb-5 pr-5">
                  <FormControl
                    v-model="settings.font_family"
                    type="select"
                    label="Font Family"
                    :options="fontOptions"
                    :description="`Choose the default font family for ${
                      tabIndex === 1 ? 'this document' : 'new documents'
                    }.`"
                  />
                  <FormControl
                    v-model="settings.font_size"
                    type="select"
                    label="Font Size"
                    :options="fontSizeOptions"
                    :description="'Set the font size  of the editor (px).'"
                  />
                  <FormControl
                    v-model="settings.line_height"
                    type="select"
                    label="Line Height"
                    :options="lineHeightOptions"
                    description="Set the line height of the editor."
                  />
                </div>
                <div class="flex flex-col gap-4 pb-5 pr-5">
                  <FormControl
                    v-if="tabIndex === 0"
                    v-model="settings.watermark_text"
                    type="text"
                    label="Watermark Text"
                    placeholder="Enter watermark text"
                    :description="`Default watermark text for ${
                      tabIndex === 1 ? 'this document' : 'new documents'
                    } when exporting to PDF.`"
                  />
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormControl
                      v-if="tabIndex === 0"
                      v-model.number="settings.watermark_size"
                      type="number"
                      label="Watermark Size (px)"
                      placeholder="40"
                      :min="10"
                      :max="300"
                      :step="5"
                      :description="`Default watermark size for ${
                        tabIndex === 1 ? 'this document' : 'new documents'
                      }.`"
                      class="w-full"
                    />
                    <FormControl
                      v-if="tabIndex === 0"
                      v-model.number="settings.watermark_angle"
                      type="number"
                      label="Watermark Angle (°)"
                      placeholder="-45"
                      :min="-180"
                      :max="180"
                      :step="15"
                      :description="`Default watermark angle for ${
                        tabIndex === 1 ? 'this document' : 'new documents'
                      }.`"
                      class="w-full"
                    />
                  </div>
                  <FormControl
                    v-if="tabIndex === 1"
                    v-model="settings.apply_watermark"
                    type="checkbox"
                    label="Apply Watermark to PDF"
                    :description="'Enable this to automatically apply watermark when downloading PDF for this document.'"
                  />
                </div>
                <!-- <FormControl
                  label="Custom Classes"
                  placeholder="font-semibold"
                  v-model="settings.custom_css"
                  description="Any additional classes to apply."
                  type="textarea"
                /> -->
                <div class="mt-2">
                  <div
                    v-if="error"
                    class="text-xs text-ink-red-4"
                  >
                    {{ error }}
                  </div>
                  <Button
                    label="Update"
                    variant="solid"
                    class="w-full mt-3"
                    :disabled="!dirty || error"
                    :loading="resource.loading"
                    @click="
                      resource.setValue.submit({ [key]: settings }),
                      setDirty(false)
                    "
                  />
                </div>
              </template>
            </Form>
          </div>
        </template>
      </Tabs>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, reactive, watchEffect } from "vue"
import { FormControl, Dialog, Tabs } from "frappe-ui"
import { FONT_FAMILIES, dynamicList } from "@/utils/files"
import Form from "@/components/Form.vue"

const open = ref(true)
const model = defineModel()

const props = defineProps({
  docSettings: { required: true, type: Object },
  globalSettings: { required: true, type: Object },
  editable: Boolean,
})
const tabs = dynamicList([
  { label: "Everywhere", icon: LucideGlobe2 },
  { label: "This document", icon: LucideFileText },
])
const tabIndex = ref(props.editable ? 1 : 0)

const fontOptions = computed(() =>
  dynamicList([
    {
      label: "Automatic",
      value: "global",
      cond: tabIndex.value === 1,
    },
    ...FONT_FAMILIES,
  ])
)
const fontSizeOptions = computed(() =>
  dynamicList([
    {
      label: "Automatic",
      value: "global",
      cond: tabIndex.value === 1,
    },
    { label: "13px", value: 13 },
    { label: "14px", value: 14 },
    { label: "15px", value: 15 },
    { label: "16px", value: 16 },
    { label: "17px", value: 17 },
    { label: "18px", value: 18 },
  ])
)

const lineHeightOptions = computed(() =>
  dynamicList([
    {
      label: "Automatic",
      value: "global",
      cond: tabIndex.value === 1,
    },
    { label: "1.2", value: "1.2" },
    { label: "1.4", value: "1.4" },
    { label: "1.5", value: "1.5" },
    { label: "1.6", value: "1.6" },
    { label: "1.8", value: "1.8" },
    { label: "2", value: "2" },
    { label: "2.5", value: "2.2" },
    { label: "2.5", value: "2.5" },
    { label: "3", value: "3" },
  ])
)

const resource = computed(() =>
  tabIndex.value === 1 ? props.docSettings : props.globalSettings
)
const key = computed(() =>
  tabIndex.value === 1 ? "settings" : "writer_settings"
)

const KEYS = ["font_family", "font_size", "line_height", "versioning", "watermark_text", "watermark_size", "watermark_angle", "apply_watermark"]

const settings = reactive({})

watchEffect(() => {
  const base = { ...resource.value.doc[key.value] }
  for (const k of KEYS) {
    if (k === "apply_watermark") {
      settings[k] = base[k] === true
    } else {
      settings[k] = base[k] || "global"
    }
  }
  if (tabIndex.value === 1) settings.collab = base.collab
})
</script>
