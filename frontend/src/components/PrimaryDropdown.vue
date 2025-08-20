<template>
  <div
    class="flex items-center justify-between gap-2"
    :class="{ 'flex-wrap': !isExpanded, 'nowrap': !isExpanded }"
    :style="{ width: isExpanded ? '100%' : 'auto' }"
  >
    <div class="flex items-center gap-2">
      <Button size="sm" variant="ghost" @click="toggleCollapsed">
        <template #icon>
          <component :is="isExpanded ? ArrowLeftFromLine : ArrowRightFromLine" class="size-5 text-black" />
        </template>
      </Button>
      <!-- <span
        class="text-lg font-semibold text-ink-gray-9"
        :class="isExpanded ? '' : 'hidden'"
      >
        Kho tài liệu
      </span> -->
    </div>
    <!-- <Button size="sm" variant="ghost" @click="showSettings = true">
      <template #icon>
        <LucideSettings class="size-4" />
      </template>
    </Button> -->
  </div>
  <SettingsDialog
    v-if="showSettings"
    v-model="showSettings"
    :suggested-tab="suggestedTab"
  />
  <ShortcutsDialog
    v-if="showShortcuts"
    v-model="showShortcuts"
  />
</template>

<script setup>
import SettingsDialog from "@/components/Settings/SettingsDialog.vue"
import ShortcutsDialog from "@/components/ShortcutsDialog.vue"
import emitter from "@/emitter"
import { Button } from "frappe-ui"
import { ref } from "vue"
import { useStore } from "vuex"
import ArrowLeftFromLine from "~icons/lucide/panel-left-close"
import ArrowRightFromLine from "~icons/lucide/panel-right-open"
const store = useStore()

const props = defineProps({
  isExpanded: Boolean,
})
const showSettings = ref(false)
const showShortcuts = ref(false)
const suggestedTab = ref(0)
emitter.on("showSettings", (val = 0) => {
  showSettings.value = true
  suggestedTab.value = val
})
emitter.on("toggleShortcuts", () => {
  showShortcuts.value = !showShortcuts.value
})

function toggleCollapsed() {
  store.commit("setIsSidebarExpanded", props.isExpanded ? false : true)
}
</script>
