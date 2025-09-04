<template>
  <Dialog
    v-model="open"
    @close="model = false"
    :options="{
      title: 'Settings',
      actions: [
        {
          label: 'Update',
          loading: resource.loading,
          onClick: () => resource.setValue.submit({ [key]: settings }),
          variant: 'solid',
        },
      ],
    }"
  >
    <template #body-content>
      <Tabs
        :tabs
        v-model="tabIndex"
      >
        <template #tab-panel="{ tab }">
          <div class="overflow-y-auto ps-1 pt-4">
            <div class="flex flex-col gap-4 pb-5 pr-5">
              <FormControl
                type="select"
                label="Font Family"
                :options="FONT_FAMILIES"
                v-model="settings.font_family"
                :description="`Choose the default font family for ${
                  tabIndex === 0 ? 'this document' : 'new documents'
                }.`"
              />
              <FormControl
                type="select"
                label="Font Size"
                :options="fontSizeOptions"
                v-model="settings.font_size"
                description="Set the font size  of the editor (px)."
              />
              <FormControl
                type="select"
                label="Line Height"
                :options="lineHeightOptions"
                v-model="settings.line_height"
                description="Set the line height of the editor ."
              />
              <FormControl
                label="Custom Classes"
                placeholder="font-semibold"
                v-model="settings.custom_css"
                description="Any additional classes to apply."
                type="textarea"
              />
            </div>
          </div>
        </template>
      </Tabs>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref } from "vue"
import { FormControl, useDoc, Dialog, Tabs } from "frappe-ui"
import { useStore } from "vuex"
import { FONT_FAMILIES } from "@/utils/files"

const store = useStore()
const open = ref(true)
const model = defineModel()

const tabIndex = ref(0)

const props = defineProps({
  docSettings: { required: true, type: Object },
})
const tabs = [
  { label: "This document", icon: LucideFileText },
  { label: "Everywhere", icon: LucideGlobe2 },
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

const globalSettings = useDoc({
  doctype: "Drive Settings",
  name: store.state.user.id,
  immediate: true,
  transform: (doc) => {
    doc.writer_settings = JSON.parse(doc.writer_settings) || {}
    return doc
  },
})
const resource = computed(() =>
  tabIndex.value === 0 ? props.docSettings : globalSettings
)
const key = computed(() =>
  tabIndex.value === 0 ? "settings" : "writer_settings"
)
const settings = computed(() => resource.value.doc[key.value])
</script>
