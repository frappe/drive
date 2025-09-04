<template>
  <div
    v-if="editor"
    class="self-stretch w-96 border-s-2 h-full overflow-hidden"
  >
    <h3
      class="px-3 border-b text-large text-ink-gray-9 font-semibold"
      :class="current ? 'p-4' : 'p-2'"
    >
      Versions
      <Button
        :icon="LucideX"
        variant="ghost"
        class="float-right"
        @click="clearSnapshot"
      />
    </h3>
    <div
      class="flex p-2 flex-col justify-start pb-5 bg-surface-white h-full overflow-y-auto pb-15"
    >
      <Button
        v-for="(version, i) in versions"
        variant="ghost"
        class="!h-12"
        :class="{ '!bg-surface-gray-4': version.name === current?.name }"
        @click="renderSnapshot(version, versions[i - 1] || null)"
        :label="
          version.title
            ? formatDate(version.title)
            : version.snapshot.slice(1, 10)
        "
      />
    </div>
  </div>
</template>
<script setup>
import * as Y from "yjs"
import {
  ySyncPlugin,
  ySyncPluginKey,
  yCursorPlugin,
  yUndoPlugin,
  undo,
  redo,
} from "y-prosemirror"
import { TiptapTransformer } from "@hocuspocus/transformer"
import { toUint8Array } from "js-base64"
import LucideX from "~icons/lucide/x"
import { ref } from "vue"
import { formatDate } from "@/utils/format"
import emitter from "@/emitter"

const props = defineProps({
  editor: Object,
  versions: Array,
})
const emit = defineEmits(["saveDocument"])
const current = defineModel()
const showVersions = defineModel("showVersions")

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
  const binding = ySyncPluginKey.getState(props.editor.view.state).binding
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
