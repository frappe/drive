<template>
  <Dialog
    v-model="open"
    :options="{
      title: __('Settings'),
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
                  {{ __("Configuration") }}
                </h3>
                <div class="flex flex-col gap-4 pb-5 pr-5">
                  <FormControl
                    v-model="settings.versioning"
                    type="number"
                    min="1"
                    :label="__('Versioning Frequency')"
                    :placeholder="__('Default')"
                    :options="[]"
                    :validate="
                      (k) =>
                        k >= 1
                          ? true
                          : __('Please give a positive whole number for versioning frequency.')
                    "
                    :description="tabIndex === 1 ? __('How often to take automated versions for this document (minutes).') : __('How often to take automated versions for new documents (minutes).')"
                  />
                </div>
                <h3 class="text-sm font-medium text-ink-gray-7 mb-3">
                  {{ __("Styles") }}
                </h3>
                <div class="flex flex-col gap-4 pb-5 pr-5">
                  <FormControl
                    v-model="settings.font_family"
                    type="select"
                    :label="__('Font Family')"
                    :options="fontOptions"
                    :description="tabIndex === 1 ? __('Choose the default font family for this document.') : __('Choose the default font family for new documents.')"
                  />
                  <FormControl
                    v-model="settings.font_size"
                    type="select"
                    :label="__('Font Size')"
                    :options="fontSizeOptions"
                    :description="__('Set the font size of the editor (px).')"
                  />
                  <FormControl
                    v-model="settings.line_height"
                    type="select"
                    :label="__('Line Height')"
                    :options="lineHeightOptions"
                    :description="__('Set the line height of the editor.')"
                  />
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
                      :label="__('Update')"
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
  { label: __("Everywhere"), icon: LucideGlobe2 },
  { label: __("This document"), icon: LucideFileText },
])
const tabIndex = ref(props.editable ? 1 : 0)

const fontOptions = computed(() =>
  dynamicList([
    {
      label: __("Automatic"),
      value: "global",
      cond: tabIndex.value === 1,
    },
    ...FONT_FAMILIES,
  ])
)
const fontSizeOptions = computed(() =>
  dynamicList([
    {
      label: __("Automatic"),
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
      label: __("Automatic"),
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

const KEYS = ["font_family", "font_size", "line_height", "versioning"]

const settings = reactive({})

watchEffect(() => {
  const base = { ...resource.value.doc[key.value] }
  for (const k of KEYS) {
    settings[k] = base[k] || "global"
  }
  if (tabIndex.value === 1) settings.collab = base.collab
})
</script>
