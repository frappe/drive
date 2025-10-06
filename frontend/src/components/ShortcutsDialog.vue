<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Keyboard Shortcuts', size: '4xl' }"
  >
    <template #body-content>
      <div
        v-focus
        class="w-full grid grid-cols-2 gap-10 py-1"
      >
        <div
          v-for="group in shortcutGroups"
          :key="group.title"
          class="border-b pb-4"
        >
          <h2 class="text-lg font-semibold text-ink-gray-8 mb-4">
            {{ group.title }}
          </h2>
          <ul class="space-y-2">
            <li
              v-for="(shortcut, index) in group.shortcuts"
              :key="index"
              class="flex items-start justify-between"
            >
              <div class="text-ink-gray-7 text-base">
                {{ shortcut[1] }}
              </div>
              <div class="flex space-x-1 w-[9rem] gap-1 justify-start">
                <span
                  v-for="(key, kIndex) in shortcut[0]"
                  :key="kIndex"
                  class="px-2 py-0.5 bg-surface-gray-2 border border-outline-gray-2 text-xs rounded-sm font-mono text-ink-gray-8 shadow-sm"
                >
                  {{ key }}
                </span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { Dialog } from "frappe-ui"
import { computed } from "vue"
const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(["update:modelValue"])

const getLabel = (key) =>
  document.querySelector(`[accesskey='${key}']`)?.accessKeyLabel

const metaKey = computed(() => {
  const platform = navigator.platform.toLowerCase()
  if (platform.includes("mac")) {
    return "⌘" // Command key
  } else if (platform.includes("win")) {
    return "⊞" // Windows key
  }
  return "Meta"
})
const shortcutGroups = [
  {
    title: "General",
    shortcuts: [
      [[metaKey.value, "K"], "Find Files"],
      [["Ctrl", ","], "Open Settings"],
    ],
  },
  {
    title: "Navigation",
    shortcuts: [
      [getLabel("i"), "Inbox"],
      [getLabel("h"), "Home"],
      [getLabel("t"), "Team"],
      [getLabel("r"), "Recents"],
      [getLabel("f"), "Favourites"],
      [getLabel("s"), "Shared"],
      [getLabel("d"), "Shared"],
    ],
  },
  {
    title: "List",
    shortcuts: [
      [[metaKey.value, "A"], "Select all"],
      [["Esc"], "Unselect all"],
      [getLabel("s"), "Share selected file(s)"],
      [getLabel("m"), "Move selected file(s)"],
      [[metaKey.value, "Delete"], "Delete selected file(s)"],
      [getLabel("u"), "Upload a file"],
      [getLabel("n"), "Create a folder"],
    ],
  },
]

const open = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit("update:modelValue", newValue)
  },
})
</script>
