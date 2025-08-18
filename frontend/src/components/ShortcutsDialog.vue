<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Keyboard Shortcuts', size: '4xl' }"
  >
    <template #body-content>
      <div class="w-full grid grid-cols-2 gap-10 py-1">
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
              <div class="flex space-x-1 w-[7rem] gap-1 justify-start">
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

const shortcutGroups = [
  {
    title: "General",
    shortcuts: [
      [["Ctrl", "K"], "Open Command Palette"],
      [["Ctrl", ","], "Open Settings"],
    ],
  },
  {
    title: "Navigation",
    shortcuts: [
      [["Alt/Option", "H"], "Home"],
      [["Alt/Option", "I"], "Inbox"],
      [["Alt/Option", "R"], "Recents"],
      [["Alt/Option", "F"], "Favourites"],
      [["Alt/Option", "S"], "Shared"],
    ],
  },
  {
    title: "List",
    shortcuts: [
      [["Alt/Option", "A"], "Select all"],
      [["Esc"], "Unselect all"],
      [["Alt/Option", "Delete"], "Delete selected file(s)"],
      [["Alt/Option", "M"], "Move selected file(s)"],
      [["Alt/Option", "U"], "Upload a file"],
      [["Alt/Option", "Shift", "U"], "Upload a folder"],
      [["Alt/Option", "Shift", "N"], "Create a folder"],
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
