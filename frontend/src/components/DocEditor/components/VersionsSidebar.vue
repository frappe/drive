<template>
  <div
    v-if="editor"
    class="self-stretch w-64 border-e h-full overflow-hidden"
  >
    <h3
      class="ps-3 p-1.5 flex items-center justify-between text-large border-b text-ink-gray-9 font-medium mb-1"
    >
      Versions
      <Button
        :icon="LucideX"
        variant="ghost"
        class="float-right"
        @click="clearSnapshot"
      />
    </h3>
    <div class="p-3.5 gap-4 flex flex-col h-full overflow-y-auto">
      <div
        v-for="[title, group] in Object.entries(groupedVersions)"
        class="flex flex-col gap-0.5 justify-start bg-surface-white"
      >
        <div class="text-ink-gray-8 text-sm font-medium mb-1">{{ title }}:</div>
        <Button
          v-for="(version, i) in group"
          :variant="version.name === current?.name ? 'solid' : 'ghost'"
          class="text-start text-sm py-4"
          @click="renderSnapshot(version, group[i - 1] || null)"
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
import { formatDate } from "@/utils/format"
import { computed } from "vue"
import emitter from "@/emitter"

const props = defineProps({
  editor: Object,
  versions: Array,
})
const emit = defineEmits(["saveDocument"])
const current = defineModel()
const showVersions = defineModel("showVersions")
const groupedVersions = computed(() =>
  props.versions.reduce((acc, version) => {
    const date = formatDate(version.title).slice(0, 8)
    if (!acc[date]) {
      acc[date] = []
    }
    acc[date].push(version)
    return acc
  }, {})
)

const renderSnapshot = (version, prevSnapshot) => {
  current.value = version
  props.editor.view.dispatch(
    props.editor.view.state.tr.setMeta(ySyncPluginKey, {
      snapshot: Y.decodeSnapshot(toUint8Array(version.snapshot)),
      prevSnapshot:
        prevSnapshot == null
          ? Y.emptySnapshot
          : Y.decodeSnapshot(toUint8Array(version.snapshot)),
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

emitter.on("restore-snapshot", () => {
  const view = props.editor.view
  view.dispatch(
    view.state.tr.setMeta(ySyncPluginKey, {
      snapshot: null,
      prevSnapshot: null,
    })
  )
  showVersions.value = false
  emit("saveDocument")
})
emitter.on("clear-snapshot", clearSnapshot)
</script>
