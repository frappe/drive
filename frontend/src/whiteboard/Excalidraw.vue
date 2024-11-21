<!-- eslint-disable vue/attribute-hyphenation -->
<template>
  <ExcalidrawComponent
    class="excalidraw"
    :onChange="
      (elements, appState, files) => handleChange(elements, appState, files)
    "
    :initialData="initialData"
    :excalidrawAPI="ExcalidrawAPI"
    :showLibrary="false"
    :viewModeEnabled="editable"
    :UIOptions="uiOptions"
  />
</template>

<script setup lang="ts">
import { Excalidraw } from "@excalidraw/excalidraw"
import { ref, computed } from "vue"
import { applyPureReactInVue } from "veaury"

const emit = defineEmits(["saveWhiteboard"])
const props = defineProps({
  entity: {
    default: null,
    type: Object,
    required: false,
  },
  content: {
    type: String,
    required: true,
  },
})

let ExcalidrawAPI
const ExcalidrawComponent = applyPureReactInVue(Excalidraw)
const initialData = ref(props.content.length ? JSON.parse(props.content) : [])
const editable = computed(() => {
  return !props.entity.write
})

const uiOptions = {
  canvasActions: {
    loadScene: false,
    changeViewBackgroundColor: false,
    toggleTheme: false,
    saveToActiveFile: false,
    saveAsImage: false,
    saveFileToDisk: false,
    export: false,
    clearCanvas: false,
  },
  dockedSidebarBreakpoint: 200,
}

function handleChange(elements, appState, files) {
  emit("saveWhiteboard", { elements, files })
}
</script>
<style>
.excalidraw {
  /* Spacing */
  --space-factor: 0.1rem;
  --default-icon-size: 1rem;
  --default-button-size: 1.5rem;
  --lg-icon-size: 1rem;
  --lg-button-size: 2rem;
  --editor-container-padding: 0.5rem;
  /* Font */
  --ui-font: InterVar;
  /* Colors */
  --color-on-primary-container: #171717;
  --color-on-surface: #171717;
  --icon-fill-color: #171717;
  --color-primary: #171717;
  --color-primary-darker: #c7c7c7;
  --color-primary-darkest: #525252;
  --color-primary-light: #f3f3f3;
  --color-surface-primary-container: #f3f3f3;
  --color-brand-hover: #f3f3f3;
  --color-brand-active: #f3f3f3;
  --button-hover-bg: #f3f3f3;
}

.excalidraw .ToolIcon .ToolIcon__keybinding {
  bottom: 0px;
  right: 3px;
  font-size: 0.5rem;
}

.excalidraw .main-menu-trigger {
  display: none;
}

.excalidraw .he .excalidraw .sidebar-trigger {
  display: none;
}
</style>
