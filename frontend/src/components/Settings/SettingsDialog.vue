<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Settings', size: '5xl' }"
  >
    <template #body>
      <div
        class="flex"
        :style="{ height: '80vh' }"
      >
        <div
          class="flex w-52 shrink-0 flex-col bg-surface-menu-bar py-3 p-4 border-r"
        >
          <h1 class="text-xl font-semibold leading-6 text-ink-gray-9 pr-2">
            {{ __("Settings") }}
          </h1>
          <div class="mt-3 space-y-1">
            <button
              v-for="tab in tabs"
              :key="tab.label"
              class="flex h-7 w-full items-center gap-2 rounded-sm px-2 py-1"
              :class="[
                activeTab?.label == tab.label
                  ? 'bg-surface-gray-4'
                  : 'hover:bg-surface-gray-2',
              ]"
              @click="activeTab = tab"
            >
              <component
                :is="tab.icon"
                class="size-4 text-ink-gray-7 stroke-[1.5]"
              />
              <span class="text-base text-ink-gray-8">
                {{ __(tab.label) }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col px-8 pt-6 overflow-y-auto">
          <component
            :is="activeTab.component"
            v-if="activeTab"
          />
        </div>
        <Button
          class="m-3 absolute right-0"
          variant="ghost"
          @click="$emit('update:modelValue', false)"
        >
          <template #icon>
            <LucideX class="size-4" />
          </template>
        </Button>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { Button, Dialog } from "frappe-ui"
import { computed, defineProps, markRaw, ref } from "vue"
// Profile removed from Settings
import LucideCloudCog from "~icons/lucide/cloud-cog"
import LucideTag from "~icons/lucide/tag"
import StorageSettings from "./StorageSettings.vue"
// import LucideUser from "~icons/lucide/user"
import TagSettings from "./TagSettings.vue"

let tabs = [
  // {
  //   enabled: true,
  //   label: __("Profile"),
  //   icon: LucideUser,
  //   component: markRaw(ProfileSettings),
  // },
  // {
  //   enabled: true,
  //   label: __("Users"),
  //   icon: LucideUserPlus,
  //   component: markRaw(UserListSettings),
  // },
  {
    label: __("Storage"),
    icon: LucideCloudCog,
    component: markRaw(StorageSettings),
  },
  {
    label: __("Tags"),
    icon: LucideTag,
    component: markRaw(TagSettings),
  },
]

const emit = defineEmits(["update:modelValue"])
const props = defineProps({
  modelValue: Boolean,
  suggestedTab: Number,
})
// Mặc định luôn mở tab Storage (index 0)
let activeTab = ref(tabs[0])

const open = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit("update:modelValue", newValue)
    // Reset về tab Storage khi đóng dialog
    if (!newValue) {
      activeTab.value = tabs[0]
    }
  },
})
</script>
