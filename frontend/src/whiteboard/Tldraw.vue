<template>
  <Tldraw
    @mount="onEditorInit"
    :hideUi="editable"
    :persistenceKey="props.entity.name"
  />
</template>

<script setup lang="ts">
import {
  debounce,
  Tldraw as TldrawReact,
  loadSnapshot,
  getSnapshot,
} from "tldraw"
import { ref, computed } from "vue"
import { useStore } from "./useStore"
import { applyPureReactInVue } from "veaury"
import "./tldraw.css"

const editorRef = ref()
const documentRef = ref()
const sessionRef = ref()
const tlStore = useStore() // fix asset store. Its b64 encoding everything right now
const Tldraw = applyPureReactInVue(TldrawReact)

const emit = defineEmits(["saveWhiteboard"])
const props = defineProps({
  entity: {
    default: null,
    type: Object,
    required: false,
  },
  content: {
    default: null,
    type: String,
    required: true,
  },
})

const editable = computed(() => {
  return !props.entity.write
})

const onEditorInit = (editor) => {
  editorRef.value = editor
  if (props.content?.length) {
    const { document, session } = JSON.parse(props.content)
    documentRef.value = document
    sessionRef.value = session
    loadSnapshot(editor.store, { document })
    loadSnapshot(editor.store, { session })
    console.log(document)
    console.log(session)
  } else {
    const { document, session } = getSnapshot(editor.store)
    documentRef.value = document
    sessionRef.value = session
  }
  editor.store.listen(debounce(save, 500), {
    source: "user",
    scope: "all",
  })
}

function save() {
  //filter out pointer and keyboard events
  const snap = getSnapshot(editorRef.value.store)
  const json = JSON.stringify(snap)
  emit("saveWhiteboard", json)
}
</script>
