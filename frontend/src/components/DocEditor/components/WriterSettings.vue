<template>
  <Dialog
    v-model="open"
    @close="model = false"
    :options="{
      title: 'Settings',
    }"
  >
    <template #body-content>
      <Tabs
        :tabs
        v-model="tabIndex"
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
                    type="number"
                    min="1"
                    label="Versioning Frequency"
                    :options="[]"
                    v-model="settings.versioning"
                    :validate="
                      (k) =>
                        k > 1
                          ? true
                          : 'Please give a positive whole number for versioning frequency.'
                    "
                    :description="`How often to take automated versions for ${
                      tabIndex === 1 ? 'this document' : 'new documents'
                    } (minutes).`"
                  />
                </div>
                <h3 class="text-sm font-medium text-ink-gray-7 mb-3">Styles</h3>
                <div class="flex flex-col gap-4 pb-5 pr-5">
                  <FormControl
                    type="select"
                    label="Font Family"
                    :options="fontOptions"
                    v-model="settings.font_family"
                    :description="`Choose the default font family for ${
                      tabIndex === 1 ? 'this document' : 'new documents'
                    }.`"
                  />
                  <FormControl
                    type="select"
                    label="Font Size"
                    :options="fontSizeOptions"
                    v-model="settings.font_size"
                    :description="'Set the font size  of the editor (px).'"
                  />
                  <FormControl
                    type="select"
                    label="Line Height"
                    :options="lineHeightOptions"
                    v-model="settings.line_height"
                    description="Set the line height of the editor."
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
import { FormControl, useDoc, Dialog, Tabs } from "frappe-ui"
import { useStore } from "vuex"
import { FONT_FAMILIES, dynamicList } from "@/utils/files"
import Form from "@/components/Form.vue"

const store = useStore()
const open = ref(true)
const model = defineModel()

const props = defineProps({
  docSettings: { required: true, type: Object },
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
    { label: "13px", value: 14 },
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

const globalSettings = useDoc({
  doctype: "Drive Settings",
  name: store.state.user.id,
  immediate: true,
  transform: (doc) => {
    doc.writer_settings = JSON.parse(doc.writer_settings) || {}
    console.log(doc.writer_settings)
    // doc.writer_settings.versioning = JSON.parse(doc.writer_settings.versioning)
    return doc
  },
})
const resource = computed(() =>
  tabIndex.value === 1 ? props.docSettings : globalSettings
)
const key = computed(() =>
  tabIndex.value === 1 ? "settings" : "writer_settings"
)

const KEYS = ["font_family", "font_size", "line_height", "versioning"]

const settings = reactive({})

watchEffect(() => {
  const base = { ...resource.value.doc[key.value] }
  for (let k of KEYS) {
    settings[k] = base[k] || "global"
  }
})
</script>
