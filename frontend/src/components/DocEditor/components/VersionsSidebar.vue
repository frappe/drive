<template>
  <div
    v-if="editor"
    class="self-stretch w-72 border-e h-full overflow-hidden relative"
  >
    <!-- <h3
      class="ps-3 p-1.5 flex items-center justify-between text-xs text-ink-gray-9 font-medium mb-1"
    ></h3> -->
    <div class="flex flex-col items-center w-full">
      <Tabs
        class="w-full"
        as="div"
        :tabs="[{ label: 'Automatic' }, { label: 'Manual' }]"
        v-model="tab"
      />
      <Button
        :icon="LucideX"
        variant="ghost"
        class="absolute right-1 top-2"
        @click="clearSnapshot"
      />
    </div>
    <div class="p-3.5 gap-4 flex flex-col h-full overflow-y-auto">
      <Button
        v-if="tab === 1"
        :icon="LucidePlus"
        @click="
          clearSnapshot(),
            createDialog({
              title: 'Create Version',
              size: 'sm',
              component: h(NewVersionDialog),
              props: { editor },
            })
        "
        class="absolute right-3 bottom-3"
        variant="outline"
      />
      <div
        v-if="
          !Object.entries(groupedVersions).length ||
          !Object.entries(groupedVersions)[0][1].length
        "
        class="text-ink-gray-5 text-sm text-center mt-1"
      >
        None yet.
      </div>
      <div
        v-else
        v-for="[title, group] in Object.entries(groupedVersions)"
        class="flex flex-col gap-0.5 justify-start bg-surface-white"
      >
        <div
          v-if="title !== 'Manual'"
          class="text-ink-gray-8 text-sm font-medium mb-1"
        >
          {{ title }}:
        </div>

        <Button
          v-for="(version, i) in group"
          :variant="version.name === current?.name ? 'solid' : 'ghost'"
          class="text-start text-sm py-4"
          @click="renderSnapshot(version)"
          :label="
            version.manual ? version.title : formatDate(version.title).slice(10)
          "
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import * as Y from "yjs"
import { ySyncPluginKey } from "y-prosemirror"
import { toUint8Array } from "js-base64"
import LucideX from "~icons/lucide/x"
import LucidePlus from "~icons/lucide/plus"
import { formatDate } from "@/utils/format"
import { computed, ref, h } from "vue"
import emitter from "@/emitter"
import { Tabs } from "frappe-ui"
import { createDialog } from "@/utils/dialogs"
import NewVersionDialog from "./NewVersionDialog.vue"

const props = defineProps({
  editor: Object,
  versions: Array,
})
const emit = defineEmits(["saveDocument", "newVersion"])
const current = defineModel()
const showVersions = defineModel("showVersions")
const groupedVersions = computed(() => {
  if (tab.value === 0) {
    return props.versions.reduce((acc, version) => {
      if (version.manual) return acc
      const date = formatDate(version.title).slice(0, 8)
      if (!acc[date]) {
        acc[date] = []
      }
      acc[date].push(version)
      return acc
    }, {})
  } else {
    return { Manual: props.versions.filter((v) => v.manual) }
  }
})
const tab = ref(1)
const renderSnapshot = (version, prevSnapshot) => {
  current.value = version
  props.editor.view.dispatch(
    props.editor.view.state.tr.setMeta(ySyncPluginKey, {
      snapshot: Y.decodeSnapshot(toUint8Array(version.snapshot)),
      prevSnapshot: Y.decodeSnapshot(toUint8Array(version.snapshot)),
    })
  )
}

const clearSnapshot = () => {
  const binding = ySyncPluginKey.getState(props.editor.view.state)?.binding
  if (binding != null) {
    binding.unrenderSnapshot()
  }
  showVersions.value = false
}

emitter.on("restore-snapshot", (details) => {
  createDialog({
    title: "Are you sure?",
    message: details.manual
      ? `You are restoring to a previous version: ${details.title}.`
      : `You are restoring the document to how it was at ${details.title}.`,
    actions: [
      {
        label: "Confirm",
        variant: "solid",
        onClick: () => {
          const view = props.editor.view
          view.dispatch(
            view.state.tr.setMeta(ySyncPluginKey, {
              snapshot: null,
              prevSnapshot: null,
            })
          )
          showVersions.value = false
          emit("saveDocument")
        },
      },
    ],
  })
})
emitter.on("clear-snapshot", clearSnapshot)
</script>
